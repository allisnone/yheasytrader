# -*- coding:utf-8 -*-
import random,math

def get_random_price(last_price,direction):
    #direction=[-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1]
    rate=round(0.1*random.random()*random.choice(direction),4)
    #rate=random.uniform(0.1,-0.05)#0.10,-0.1)
    random_close=round(last_price*(1+rate),2)
    #print('last_price=',last_price)
    #print('rate=',rate)
    #print('random_close=',random_close)
    return random_close

def get_direction(count=100,pos_rate=0.5):
    di1=int(count*pos_rate)*[1]+int(count*(1-pos_rate))*[-1]
    return di1

def get_continue_close(last_price=10.0,random_type=0):
    """获取符合正态分布的涨幅比例,值在 -0.1~0.1之间
    :param last_price: 平均值
    :param random_typ 随机类型，0位均匀分布，1为正态分布"""
    di=get_direction(count=100, pos_rate=0.54)
    #print(di)
    count=0
    direction=[-1,1]
    rate_list=[]
    count_5=0
    rate_last=1.0
    buy=1
    while True:
        #print('count=',count)
        if random_type==1:
            """
            rate=get_random_normal(u=0.0)
            if count==0:
                rate_last=rate
                if rate<0:
                    buy=1
            else:
                random_close=round(last_price*(1+rate*0.01),2)
            rate_list.append(rate)
            if abs(rate)<5.0:
                count_5=count_5+1
            """
            rate=get_random_normal(u=0.0)
            random_close=round(last_price*(1+rate*0.01),2)
            rate_list.append(rate)
            if abs(rate)<5.0:
                count_5=count_5+1
            
        elif random_type==0:
            random_close=get_random_price(last_price,di)
        last_price=random_close
        count=count+1
        if count>1000:
            break
    print('rate_list=%s' %rate_list)
    print('count_5=%s'%count_5)
    return last_price

def get_average():
    j=0
    final_list=[]
    for i in range(1,1000):
        last_price=10.0
        final_price=get_continue_close(last_price,1)
        print('final_price=',final_price)
        final_list.append(final_price)
        if final_price>last_price:
            j=j+1
    print('j=',j)
    if final_list:
        print('average=',sum(final_list)/len(final_list))
        
        
def get_random_normal(u=0.0):
    """获取符合正态分布的涨幅比例,值在 -0.1~0.1之间
    :param u: 平均值
    :return 随机涨幅"""
    delta=0.1/2.58
    rate_v=random.normalvariate(u,delta)
    if abs(rate_v)>=0.1:
        rate_v=rate_v/abs(rate_v)*0.1
    rate_v=round(rate_v*100.0,2)
    return rate_v

get_average()
    