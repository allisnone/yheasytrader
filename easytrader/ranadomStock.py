# -*- coding:utf-8 -*-
import random,math

def get_random_price(last_price,direction):
    #direction=[-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1,-1,1]
    rate=round(0.1*random.random()*random.choice(direction),4)
    #rate=random.uniform(0.1,-0.05)#0.10,-0.1)
    random_close=round(last_price*(1+rate),2)
    print('last_price=',last_price)
    print('rate=',rate)
    print('random_close=',random_close)
    return random_close

def get_direction(count=100,pos_rate=0.5):
    di1=int(count*pos_rate)*[1]+int(count*(1-pos_rate))*[-1]
    return di1

def get_continue_close(last_price=10.0):
    di=get_direction(count=100, pos_rate=0.51)
    print(di)
    count=0
    direction=[-1,1]
    while True:
        print('count=',count)
        random_close=get_random_price(last_price,di)
        last_price=random_close
        count=count+1
        if count>1000:
            break
    
    return last_price

j=0
final_list=[]
for i in range(1,100):
    last_price=10.0
    final_price=get_continue_close(last_price)
    print('final_price=',final_price)
    final_list.append(final_price)
    if final_price>last_price:
        j=j+1
print('j=',j)
if final_list:
    print('average=',sum(final_list)/len(final_list))
    
    