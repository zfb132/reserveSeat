#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: 'zfb'
# time: 18-09-13 22:55:35
from qcloudsms_py import SmsSingleSender
from qcloudsms_py.httpclient import HTTPError
import pymysql

import json
import requests
import datetime
import time
import random

import config
import SQLHelper

# 报头
headers = {
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 ",
    'Host':"seat.lib.whu.edu.cn"
}
# 预约系统网址
url_base = "http://seat.lib.whu.edu.cn"

# 向某个指定号码发送特定内容的消息
def sendSMS(number,params):
    ssender = SmsSingleSender(config.APPID, config.APPKEY)
    try:
        result = ssender.send_with_param(86, number, config.TEMPLATE_ID, 
                params, sign=config.SMS_SIGN, extend="", ext="")
    except HTTPError as e:
        print(json.dumps(e, ensure_ascii=False))
    except Exception as e:
        print(json.dumps(e, ensure_ascii=False))
    print(json.dumps(result, ensure_ascii=False))
    
# 登录预约系统
def login(user,pwd):
    url = url_base + "/rest/auth?username={}&password={}".format(user,pwd)
    result = requests.get(url, headers=headers)
    status = json.loads(result.text)['status']
    if(status == 'success'):
        token = json.loads(result.text)['data']['token']
        print(token)
        return token
    else:
        raise Exception('登录异常：'+json.loads(result.text)['message'])
        
# 获得预约历史记录
# offset从1开始，每次获取10条记录
def getHistory(offset,token):
    url = url_base + "/rest/v2/history/{}/10?token={}".format(offset,token)
    result = requests.get(url, headers=headers)
    status = json.loads(result.text)['status']
    if(status == 'success'):
        history = json.loads(result.text)['data']['reservations']
        return history
    else:
        raise Exception('查询历史记录异常：'+json.loads(result.text)['message'])

# 获取当前预约信息
def getReservations(token):
    url = url_base + "/rest/v2/user/reservations?token={}".format(token)
    result = requests.get(url, headers=headers)
    status = json.loads(result.text)['status']
    if(status == 'success'):
        reservations = json.loads(result.text)['data']
        return reservations
    else:
        raise Exception('获取预约信息异常：'+json.loads(result.text)['message'])
        
# 获取房间楼层信息
def getRoomsInfo(token):
    url = url_base + "/rest/v2/free/filters?token={}".format(token)
    result = requests.get(url, headers=headers)
    status = json.loads(result.text)['status']
    if(status == 'success'):
        data = json.loads(result.text)['data']
        # 键为id，值为名称
        buildings = {}
        for build in data['buildings']:
            buildings[build[0]] = build[1]
        # 键为id，值为list包括名称，建筑、楼层
        rooms= {}
        for room in data['rooms']:
            rooms[room[0]] = [room[1], buildings[room[2]], room[3]]
        return rooms
    else:
        raise Exception('获取房间信息异常：'+json.loads(result.text)['message'])
        
# 存储某个房间内当前所有座位信息
def saveSeatsInfoOfRoom(id,date,token,roomInfo):
    print('正在获取位于{}{}楼的{}的座位信息'.format(roomInfo[1],roomInfo[2],roomInfo[0]))
    url = url_base + "/rest/v2/room/layoutByDate/{}/{}?token={}".format(id,date,token)
    result = requests.get(url, headers=headers)
    status = json.loads(result.text)['status']
    if(status == 'success'):
        data = json.loads(result.text)['data']['layout']
        seats = {}
        try:
            db = pymysql.connect(host='localhost',user='root', 
                password=config.SQLPWD, db=config.DBNAME, port=3306, charset='utf8')
            cursor = db.cursor()
            for k in data:
                # 判断data字典的值（也是一个字典）的长度大于2才统计，否则说明为empty
                seat = data[k]
                #print(seat.values())
                if(len(seat)>2):
                    # 开始座位信息插入到数据库
                    try:
                        cursor.execute(
                            "insert into seat values ({},'{}','{}','{}','{}',{},{},{},{},{},'{}',{},'{}')".format(
                        seat['id'],seat['name'],k,seat['type'],seat['status'],seat['window'],
                        seat['power'],seat['computer'],seat['local'],roomInfo[2],roomInfo[0],roomInfo[3],roomInfo[1])
                        )
                    except Exception as e:
                        print(str(seat)+'\n'+str(roomInfo))
                        print(repr(e))
            # 必须有这一句
            cursor.execute("commit")
            cursor.close()
            db.close()
        except Exception as e:
            print(repr(e))
    else:
        raise Exception('获取座位信息异常：'+json.loads(result.text)['message'])
        
# 预约指定座位        
def reserveSeat(token,seat,date,stime=config.STIME,etime=config.ETIME):
    url = url_base + "/rest/v2/freeBook"
    bookParams = {}
    bookParams['token'] = token
    bookParams['seat'] = seat
    bookParams['date'] = date
    bookParams['startTime'] = stime
    bookParams['endTime'] = etime
    result = requests.post(url, params=bookParams, headers=headers)
    print(result.text)
    status = json.loads(result.text)['status']
    if(status == 'success'):
        return [True,json.loads(result.text)['data']]
    else:
        raise Exception('预约出现异常：'+json.loads(result.text)['message'])

# 取消指定id的预约
def cancelSeat(token,id):
    url = url_base + "/rest/v2/cancel/{}?token={}".format(id,token)
    result = requests.get(url, headers=headers)
    status = json.loads(result.text)['status']
    if(status == 'success'):
        return True
    else:
        raise Exception('取消预约异常：'+json.loads(result.text)['message'])

# 按时间筛选：date的格式2018-10-23 begin的示例600 roomIDs是list，按照优先级排序
def searchSeatByTime(date,begin,end,roomIDs,token):
    url = url_base + "/rest/v2/searchSeats/{}/{}/{}".format(date,begin,end)
    # 所有符合条件的座位ID
    seatIDs=[]
    searchParams = {}
    # 默认信息学部图书馆
    searchParams['buildingId'] = 1
    searchParams['batch'] = 9999
    searchParams['token'] = token
    # 每个房间都要搜索
    for room in roomIDs:
        searchParams['roomId'] = room
        result = requests.post(url,params=searchParams,headers=headers)
        #print(result.text)
        status = json.loads(result.text)['status']
        if(status == True):
            data = json.loads(result.text)['data']['seats']
            # 若无空闲座位则进行下一个房间
            if(len(data)<1):
                print('房间{}无空闲座位'.format(room))
                continue
            for k in data:
                seat = data[k]
                seatIDs.append(seat['id'])
        else:
            print('搜索出错！')
    print(seatIDs)
    return seatIDs

# 自动按时间筛选并预约
def autoSearchBookByTime(startTime=[8,30],endTime=[21,0]):
    # 登录预约系统
    try:
        token = login(config.USER,config.PASSWORD)
    except Exception as e:
        print(e)
    date = str(datetime.date.today())
    # 最大尝试次数
    num = 100
    stime = startTime[0]*60 + startTime[1]
    etime = endTime[0]*60 + endTime[1]
    while(num):
        IDs = searchSeatByTime(date,stime,etime,[14,16],token)
        print('本次搜索到空闲座位：' + ''.join(map(str,IDs)))
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
        wait = random.randint(30,100)
        print('{}s后进行下次尝试'.format(wait))
        time.sleep(wait)
    # 将相关信息发送到手机
    params = ['zfb',message]
    print('----\n'+message)
    #sendSMS(config.PHONE_NUMBER,params)


# 自动预约心仪的座位
def autoBookFavorite():
    normal = True
    isBooked = False
    # 登录预约系统
    try:
        token = login(config.USER,config.PASSWORD)
    except Exception as e:
        normal = False
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
                    print(e)
                    pass
        # 预约成功
        if(isBooked):
            # 由于返回的参数是list类型，修改后的res才是dict类型
            #print(result[1])
            res = result[1]
            message = "{}\n{}--{}\n{}".format(res['receipt'],res['begin'],res['end'],res
['location'])
            #print(message)
        else:
            message = '-1。\n预约失败！！！'
    else:
        message = '-1。\n登录出现问题！！！'
    # 将相关信息发送到手机
    params = ['zfb',message]
    print('----\n'+message)
    sendSMS(config.PHONE_NUMBER,params)
    #getHistory(1,token)


if __name__ == '__main__':
    autoSearchBookByTime([14,30],[21,30])
    #autoBookFavorite()
'''
    normal = True
    isBooked = False
    # 登录预约系统
    try:
        token = login(config.USER,config.PASSWORD)
    except Exception as e:
        normal = False
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
    print('----\n'+message)
    sendSMS(config.PHONE_NUMBER,params)
    #getHistory(1,token)
    
'''
