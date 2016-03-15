# -*- coding:utf-8 -*-
import random

def get_random_price(last_price,direction):
    #direction=[-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1]
    rate=round(0.1*random.random()*random.choice(direction),4)
    #rate=random.uniform(0.1,-0.05)#0.10,-0.1)
    random_close=round(last_price*(1+rate),2)
    print('last_price=',last_price)
    print('rate=',rate)
    print('random_close=',random_close)
    return random_close


last_price=10.0
count=0
direction=[-1,1]
while True:
    print('count=',count)
    random_close=get_random_price(last_price)
    last_price=random_close
    count=count+1
    if count>1000:
        break
    