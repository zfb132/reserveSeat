#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: 'zfb'
# time: 18-09-13 22:55:35
from qcloudsms_py import SmsSingleSender
from qcloudsms_py.httpclient import HTTPError

import json
import requests
import datetime
import time
import random
import sys

import config
from log import initLog
from reserveSeat import *

logging = initLog('reserve.log','reserve')

# 自动按时间筛选并预约
def autoSearchBookByTime(date,token,startTime=[8,30],endTime=[21,0]):
    # 最大尝试次数
    num = 5000
    stime = startTime[0]*60 + startTime[1]
    etime = endTime[0]*60 + endTime[1]
    # booked为True表示预约成功
    booked = False
    while(num and not booked):
        IDs = searchSeatByTime(date,stime,etime,[16,14],token)
        log = '本次搜索到空闲座位：' + ','.join(map(str,IDs))
        logging.debug(log)
        print(log)
        # 最多更换五次，之后就重新获取空闲座位
        for i in range(5):
            if(len(IDs) > 0):
                # 预约中间的一个
                index = int(len(IDs)/2)
                logging.debug('将要预约第{}个，座位是{}'.format(index,IDs[index]))
                try:
                    result = reserveSeat(token,IDs[index],date,stime,etime)
                    if(result[0]):
                        res = result[1]
                        message = "{}\n{}--{}\n{}".format(res['receipt'],res['begin'],res['end'],res['location'])
                        booked = True
                        break;
                    else:
                        message = '-1。\n预约失败！！！'
                except Exception as e:
                    print("预约此座位异常，重新预约")
                    logging.error("预约此座位异常，重新预约")
                # 删除已经尝试过的座位
                IDs.pop(index)
            else:
                break
        if(booked):
            break;
        num = num - 1
        # 随机等待30s-100s
        wait = random.randint(1,5)
        log = '{}s后进行下次尝试'.format(wait)
        logging.debug(log)
        print(log)
        time.sleep(wait)
    # 将相关信息发送到手机
    params = ['zfb',message]
    logging.debug('----\n'+message)
    print('----\n'+message)
    sendSMS(config.PHONE_NUMBER,params)


# 自动预约心仪的座位
def autoBookFavorite():
    normal = True
    isBooked = False
    # 登录预约系统
    try:
        token = login(config.USER,config.PASSWORD)
    except Exception as e:
        normal = False
        logging.error(e)
        print(e)
    # 获取及写入座位信息
    #rooms = getRoomsInfo(token)
    #dateToday = str(datetime.date.today())
    #for room in rooms:
    #    rooms[room].append(room)
    #    saveSeatsInfoOfRoom(room, dateToday, token, rooms[room])

    # 开始预约流程
    if(normal):
        res = getReservations(token)
        # 如果当前存在预约信息则退出程序
        if res:
            logging.debug('已有预约，程序将退出')
            print('已有预约，程序将退出')
            exit(1)
        try:
            # 获取明天日期
            date = str(datetime.date.today() + datetime.timedelta(days = 1))
            #date = str(datetime.date.today())
            result = reserveSeat(token,config.SEATID,date)
            isBooked = result[0]
        except Exception as e:
            # 如果预约失败
            for i in ['3644','3645','3670','3671']:
                # 延时0.5s
                time.sleep(0.5)
                try:
                    result = reserveSeat(token,str(i),date)
                    isBooked = result[0]
                    if(isBooked):
                        break;
                except Exception as e:
                    logging.error(e)
                    print(e)
                    pass
        # 预约成功
        if(isBooked):
            # 由于返回的参数是list类型，修改后的res才是dict类型
            #print(result[1])
            res = result[1]
            message = "{}\n{}--{}\n{}".format(res['receipt'],res['begin'],res['end'],res['location'])
            #print(message)
        else:
            message = '-1。\n预约失败！！！'
    else:
        message = '-1。\n登录出现问题！！！'
    # 将相关信息发送到手机
    params = ['zfb',message]
    logging.debug('----\n'+message)
    print('----\n'+message)
    sendSMS(config.PHONE_NUMBER,params)

if __name__ == '__main__':
    logging.debug('进入主函数')
    # 登录预约系统
    try:
        token = login(config.USER,config.PASSWORD)
    except Exception as e:
        logging.error(e)
        sys.exit("登录失败，请检查用户名或密码")
    logging.debug('登录成功')
    # 如果当前存在预约信息则退出程序
    # res为空未必无预约，还需通过history中第一条记录的status判断
    res = getReservations(token)
    if res:
        logging.error('已有预约，程序将退出')
        sys.exit('已有预约，程序将退出')
    # 当前时间是否达到22:44:59
    now = int(time.strftime('%H%M%S'))
    # 默认预约第二天，当01:00:00-22:00:00之间预约当天
    today = str(datetime.date.today())
    tomorrow = str(datetime.date.today() + datetime.timedelta(days = 1))
    if( now > 10000 and now < 220000 ):
        date = today
    elif( now > 224459 and now < 235000 ):
        date = tomorrow
    elif(now>=220000 and now <= 224459):
        date = tomorrow
        # 之前的方案好像有bug ?
        t = datetime.datetime.now()
        st = '{}-{}-{} {}:{}:{}'.format(t.year,t.month,t.day,22,45,1)
        startTime = datetime.datetime.strptime(st, "%Y-%m-%d %H:%M:%S")
        logging.debug('休眠{}s'.format((startTime-t).seconds))
        for i in range((startTime-t).seconds):
            time.sleep(1)
            #当前时间是否达到22:44:59
            now = int(time.strftime('%H%M%S'))
            if(now > 224459):
                logging.debug('等待第{}个1s时break'.format(i))
                break
        logging.debug('休眠结束')
    else:
        # 不可预约的时间段
        logging.error("非法时间段，不可预约")
        sys.exit("非法时间段，不可预约")
    logging.debug('开始运行自动搜索预约函数')
    # sys.argv[0]表示脚本名
    if(len(sys.argv)>1):
        mytime = list(map(int,sys.argv[1:len(sys.argv)]))
        autoSearchBookByTime(date,token,mytime[0:2],mytime[2:4])
    else:
        autoSearchBookByTime(date,token,[9,0],[21,30])
