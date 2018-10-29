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
import logging
import sys

import config
from reserveSeat import *

LOG_FORMAT = "%(asctime)s [%(funcName)s: %(filename)s,%(lineno)d] - %(levelname)s : %(message)s"
DATE_FORMAT = "%m/%d/%Y %H:%M:%S"
logging.basicConfig(filename='reserve.log', level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)

# 自动按时间筛选并预约
def autoSearchBookByTime(date,token,startTime=[8,30],endTime=[21,0]):
    # 最大尝试次数
    num = 5000
    print(startTime)
    stime = startTime[0]*60 + startTime[1]
    etime = endTime[0]*60 + endTime[1]
    while(num):
        IDs = searchSeatByTime(date,stime,etime,[16,14],token)
        log = '本次搜索到空闲座位：' + ''.join(map(str,IDs))
        logging.debug(log)
        print(log)
        if(len(IDs) > 0):
            result = reserveSeat(token,IDs[0],date,stime,etime)
            if(result[0]):
                res = result[1]
                message = "{}\n{}--{}\n{}".format(res['receipt'],res['begin'],res['end'],res['location'])
                break;
            else:
                message = '-1。\n预约失败！！！'
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
    # 登录预约系统
    try:
        token = login(config.USER,config.PASSWORD)
    except Exception as e:
        logging.error(e)
        print(e)
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
        time.sleep(224459-now)
    else:
        # 不可预约的时间段
        sys.exit("非法时间段，不可预约")
    # sys.argv[0]表示脚本名
    if(len(sys.argv)>1):
        mytime = list(map(int,sys.argv[1:len(sys.argv)]))
        autoSearchBookByTime(date,token,mytime[0:2],mytime[2:4])
    else:
        autoSearchBookByTime(date,token,[9,0],[21,30])
