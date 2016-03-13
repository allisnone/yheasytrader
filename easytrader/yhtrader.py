# coding: utf-8
from __future__ import division

import json
import os,datetime
import random
import re

import requests

from . import helpers
from .webtrader import WebTrader, NotLoginError

log = helpers.get_logger(__file__)

VERIFY_CODE_POS = 0
TRADE_MARKET = 1
HOLDER_NAME = 0


class YHTrader(WebTrader):
    config_path = os.path.dirname(__file__) + '/config/yh.json'

    def __init__(self):
        super(YHTrader, self).__init__()
        self.cookie = None
        self.account_config = None
        self.s = None
        self.exchange_stock_account = dict()

    def login(self, throw=False):
        print('login time0: ', datetime.datetime.now())
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        }
        if self.s is not None:
            self.s.get(self.config['logout_api'])
        print('login time00: ', datetime.datetime.now())
        self.s = requests.session()
        self.s.headers.update(headers)
        print('login time01: ', datetime.datetime.now())
        data = self.s.get(self.config['login_page'])
        print('login time02: ', datetime.datetime.now())
        # 查找验证码
        search_result = re.search(r'src=\"verifyCodeImage.jsp\?rd=([0-9]{4})\"', data.text)
        if not search_result:
            log.debug("Can not find verify code, stop login")
            return False
        print('login time1: ', datetime.datetime.now())
        verify_code = search_result.groups()[VERIFY_CODE_POS]
        print('login time10: ', datetime.datetime.now())
        if not verify_code:
            return False

        login_status, result = self.post_login_data(verify_code)
        print('login time2: ', datetime.datetime.now())
        if login_status is False and throw:
            raise NotLoginError(result)
        exchangeinfo = list((self.do(dict(self.config['account4stock']))))
        if len(exchangeinfo) >= 2:
            for i in range(2):
                if exchangeinfo[i][TRADE_MARKET]['交易市场'] == '深A':
                    self.exchange_stock_account['0'] = exchangeinfo[i][HOLDER_NAME]['股东代码'][0:10]
                else:
                    self.exchange_stock_account['1'] = exchangeinfo[i][HOLDER_NAME]['股东代码'][0:10]
        print('login time3: ', datetime.datetime.now())
        return login_status

    def post_login_data(self, verify_code):
        print(self.account_config)
        print(type(self.account_config))
        login_params = dict(
                self.config['login'],
                mac=helpers.get_mac(),
                clientip='',
                inputaccount=self.account_config['inputaccount'],
                trdpwd=self.account_config['trdpwd'],
                checkword=verify_code
        )
        log.debug('login params: %s' % login_params)
        login_response = self.s.post(self.config['login_api'], params=login_params)
        log.debug('login response: %s' % login_response.text)

        if login_response.text.find('success') != -1:
            return True, None
        return False, login_response.text

    @property
    def token(self):
        return self.cookie['JSESSIONID']

    @token.setter
    def token(self, token):
        self.cookie = dict(JSESSIONID=token)
        self.keepalive()

    def cancel_entrust(self, entrust_no, stock_code):
        """撤单
        :param entrust_no: 委托单号
        :param stock_code: 股票代码"""
        need_info = self.__get_trade_need_info(stock_code)
        cancel_params = dict(
                self.config['cancel_entrust'],
                orderSno=entrust_no,
                secuid=need_info['stock_account']
        )
        cancel_response = self.s.post(self.config['trade_api'], params=cancel_params)
        log.debug('cancel trust: %s' % cancel_response.text)
        return True

    # TODO: 实现买入卖出的各种委托类型
    def buy(self, stock_code, price, amount=0, volume=0, entrust_prop=0):
        """买入股票
        :param stock_code: 股票代码
        :param price: 买入价格
        :param amount: 买入股数
        :param volume: 买入总金额 由 volume / price 取整， 若指定 price 则此参数无效
        :param entrust_prop: 委托类型，暂未实现，默认为限价委托
        """
        params = dict(
                self.config['buy'],
                bsflag='0B',  # 买入0B 卖出0S
                qty=amount if amount else volume // price // 100 * 100
        )
        return self.__trade(stock_code, price, entrust_prop=entrust_prop, other=params)

    def sell(self, stock_code, price, amount=0, volume=0, entrust_prop=0):
        """卖出股票
        :param stock_code: 股票代码
        :param price: 卖出价格
        :param amount: 卖出股数
        :param volume: 卖出总金额 由 volume / price 取整， 若指定 amount 则此参数无效
        :param entrust_prop: 委托类型，暂未实现，默认为限价委托
        """
        params = dict(
                self.config['sell'],
                bsflag='0S',  # 买入0B 卖出0S
                qty=amount if amount else volume // price
        )
        return self.__trade(stock_code, price, entrust_prop=entrust_prop, other=params)
    
    def sell_to_exit(self, stock_code, exit_price, amount=0, volume=0, entrust_prop=0):
        """止损卖出股票
        :param stock_code: 股票代码
        :param exit_price: 止损卖出价格
        :param amount: 卖出股数
        :param volume: 卖出总金额 由 volume / price 取整， 若指定 amount 则此参数无效
        :param entrust_prop: 委托类型，暂未实现，默认为限价委托
        """
        if stock_code not in self.position.keys():
            return
        available_share_to_sell=int(self.position[stock_code]['股份可用'])
        last_close,realtime_price=self.get_realtime_stock(stock_code)
        if realtime_price<exit_price:
            log.debug('股票  %s 达到止损价格 : %s,止损退出  %s股' % (stock_code,exit_price,amount))
            params = dict(
                    self.config['sell'],
                    bsflag='0S',  # 买入0B 卖出0S
                    qty=min(amount,available_share_to_sell) if amount else available_share_to_sell
            )
            self.__trade(stock_code, last_close, entrust_prop=-1, other=params)
        else:
            pass

    def fundpurchase(self, stock_code, amount=0):
        """基金申购
        :param stock_code: 基金代码
        :param amount: 申购份额
        """
        params = dict(
                self.config['fundpurchase'],
                price=1,  # 价格默认为1
                qty=amount
        )
        return self.__tradefund(stock_code, other=params)

    def fundredemption(self, stock_code, amount=0):
        """基金赎回
        :param stock_code: 基金代码
        :param amount: 赎回份额
        """
        params = dict(
                self.config['fundredemption'],
                price=1,  # 价格默认为1
                qty=amount
        )
        return self.__tradefund(stock_code, other=params)

    def fundsubscribe(self, stock_code, amount=0):
        """基金认购
        :param stock_code: 基金代码
        :param amount: 认购份额
        """
        params = dict(
                self.config['fundsubscribe'],
                price=1,  # 价格默认为1
                qty=amount
        )
        return self.__tradefund(stock_code, other=params)

    def fundsplit(self, stock_code, amount=0):
        """基金分拆
        :param stock_code: 母份额基金代码
        :param amount: 分拆份额
        """
        params = dict(
                self.config['fundsplit'],
                qty=amount
        )
        return self.__tradefund(stock_code, other=params)

    def fundmerge(self, stock_code, amount=0):
        """基金合并
        :param stock_code: 母份额基金代码
        :param amount: 合并份额
        """
        params = dict(
                self.config['fundmerge'],
                qty=amount
        )
        return self.__tradefund(stock_code, other=params)

    def __tradefund(self, stock_code, other):
        # 检查是否已经掉线
        if not self.heart_thread.is_alive():
            check_data = self.get_balance()
            if type(check_data) == dict:
                return check_data
        need_info = self.__get_trade_need_info(stock_code)
        trade_params = dict(
                other,
                stockCode=stock_code,
                market=need_info['exchange_type'],
                secuid=need_info['stock_account']
        )

        trade_response = self.s.post(self.config['trade_api'], params=trade_params)
        log.debug('trade response: %s' % trade_response.text)
        return True
    
    def get_realtime_stock(self,stock_code):
        return last_close,realtime_price
    
    def __trade(self, stock_code, price, entrust_prop, other):
        """
        :param stock_code: 股票代码
        :param price: 交易限价挂单价格，如果entrust_prop=1或者-1，为上一个交易的交易价格，用于即时卖卖
        :param amount: 卖出股数
        :param volume: 卖出总金额 由 volume / price 取整， 若指定 amount 则此参数无效
        :param entrust_prop: 委托类型，暂未实现，默认为限价委托
        """
        # 检查是否已经掉线
        if not self.heart_thread.is_alive():
            check_data = self.get_balance()
            if type(check_data) == dict:
                return check_data
        need_info = self.__get_trade_need_info(stock_code)
        if entrust_prop==1:#主动即时买入，以涨停价买入
            price=round(price*1.1,2)
        elif entrust_prop==-1: #主动即时卖出，以跌停价卖
            price=round(price*0.9,2)
        else:
            pass
        trade_params = dict(
                other,
                stockCode=stock_code,
                price=price,
                market=need_info['exchange_type'],
                secuid=need_info['stock_account']
        )
        trade_response = self.s.post(self.config['trade_api'], params=trade_params)
        log.debug('trade response: %s' % trade_response.text)
        return trade_response.text

    def __get_trade_need_info(self, stock_code):
        """获取股票对应的证券市场和帐号"""
        # 获取股票对应的证券市场
        sh_exchange_type = '1'
        sz_exchange_type = '0'
        exchange_type = sh_exchange_type if helpers.get_stock_type(stock_code) == 'sh' else sz_exchange_type
        return dict(
                exchange_type=exchange_type,
                stock_account=self.exchange_stock_account[exchange_type]
        )

    def create_basic_params(self):
        basic_params = dict(
                CSRF_Token='undefined',
                timestamp=random.random(),
        )
        return basic_params

    def request(self, params):
        url = self.trade_prefix + params['service_jsp']
        r = self.s.get(url, cookies=self.cookie)
        if params['service_jsp'] == '/trade/webtrade/stock/stock_zjgf_query.jsp':
            if params['service_type'] == 2:
                rptext = r.text[0:r.text.find('操作')]
                return rptext
            else:
                rbtext = r.text[r.text.find('操作'):]
                rbtext += 'yhposition'
                return rbtext
        else:
            return r.text

    def format_response_data(self, data):
        # 需要对于银河持仓情况特殊处理
        if data.find('yhposition') != -1:
            search_result_name = re.findall(r'<td nowrap=\"nowrap\" class=\"head(?:\w{0,5})\">(.*)</td>', data)
            search_result_content = re.findall(r'<td nowrap=\"nowrap\"  >(.*)</td>', data)
            print('search_result_name=',search_result_name)
            if '参考成本价' in search_result_name:
                search_result_name.remove('参考成本价')
            else:
                 pass
        else:
            # 获取原始data的html源码并且解析得到一个可读json格式 
            search_result_name = re.findall(r'<td nowrap=\"nowrap\" class=\"head(?:\w{0,5})\">(.*)</td>', data)
            search_result_content = re.findall(r'<td nowrap=\"nowrap\">(.*)&nbsp;</td>', data)

        columnlen = len(search_result_name)
        if columnlen == 0 or len(search_result_content) % columnlen != 0:
            log.error("Can not fetch balance info")
            retdata = json.dumps(search_result_name)
            retjsonobj = json.loads(retdata)
        else:
            rowlen = len(search_result_content) // columnlen
            retdata = list()
            for i in range(rowlen):
                retrowdata = list()
                for j in range(columnlen):
                    retdict = dict()
                    retdict[search_result_name[j]] = search_result_content[i * columnlen + j]
                    retrowdata.append(retdict)
                retdata.append(retrowdata)
            retlist = json.dumps(retdata)
            retjsonobj = json.loads(retlist)
        return retjsonobj

    def fix_error_data(self, data):
        return data

    def check_login_status(self, return_data):
        pass

    def check_account_live(self, response):
        if hasattr(response, 'get') and response.get('error_no') == '-1':
            self.heart_active = False
            
    def list2dict(self,list_nesting_dict):
        """嵌套着字典的 list 转化为字典 """
        this_dict={}
        for ls in list_nesting_dict:
            this_dict.update(ls)
        return this_dict
  
    def get_balance(self):
        """获取账户资金状况"""
        #return self.do(self.config['balance'])
        balance_list=self.do(self.config['balance'])
        if balance_list:
            return self.list2dict(balance_list[0])
        else:
            return {}

    def get_position(self):
        """获取持仓"""
        #return self.do(self.config['position'])
        position_list=self.do(self.config['position'])
        position_dict={}
        for pos in position_list:
            absolute_loss=pos[7]['参考盈亏']
            absolute_loss_v=absolute_loss[(absolute_loss.find('>')+1):-7]
            pos[7]['参考盈亏']=absolute_loss_v
            absolute_loss_rate=pos[8]['盈亏比例(%)']
            absolute_loss_rate_v=absolute_loss_rate[(absolute_loss_rate.find('>')+1):-7]
            #print('absolute_loss_rate_v=',absolute_loss_rate_v)
            pos[8]['盈亏比例(%)']=absolute_loss_rate_v
            symbole_dict=pos.pop(1)
            position_dict[symbole_dict['证券代码']]=self.list2dict(pos)
        return position_dict
