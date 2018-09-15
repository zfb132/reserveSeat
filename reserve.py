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

import config
import SQLHelper

# 报头
headers = {
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 ",
    'Host':"seat.lib.whu.edu.cn"
}
# 预订座位url的参数
bookParams = {
    'token':'',
    'startTime':config.STIME,
    'endTime':config.ETIME,
    'seat':config.SEATID,
    'date':''
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
                            "insert into seat values ({},'{}','{}','{}',{},{},{},{},{},'{}',{},'{}')".format(
                        seat['id'],seat['name'],seat['type'],seat['status'],seat['window'],
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
def reserveSeat(token,seat,date):
    url = url_base + "/rest/v2/freeBook"
    bookParams['token'] = token
    bookParams['seat'] = seat
    bookParams['date'] = date
    result = requests.post(url, params=bookParams, headers=headers)
    print(result.text)
    status = json.loads(result.text)['status']
    if(status == 'success'):
        return True
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
        
if __name__ == '__main__':
    SQLHelper.initDataBase()
    SQLHelper.initTable()
    normal = True
    isBooked = False
    # 登录预约系统
    try:
        token = login(config.USER,config.PASSWORD)
    except Exception as e:
        normal = False
        print(e)
    # 获取及写入座位信息
    rooms = getRoomsInfo(token)
    dateToday = str(datetime.date.today())
    for room in rooms:
        rooms[room].append(room)
        saveSeatsInfoOfRoom(room, dateToday, token, rooms[room])

    # 开始预约流程
    if(normal):
        res = getReservations(token)
        # 如果当前存在预约信息则退出程序
        if res:
            print('已有预约，程序将退出')
            exit(1)
        try:
            # 获取明天日期
            #date = str(datetime.date.today() + datetime.timedelta(days = 1))
            date = str(datetime.date.today())
            isBooked = reserveSeat(token,config.SEATID,date)
        except Exception as e:
            # 如果预约失败
            for i in range(-15,10):
                # 延时0.5s
                time.sleep(0.5)
                try:
                    isBooked = reserveSeat(token,str(i+int(config.SEATID)),date)
                    if(isBooked):
                        break;
                except Exception as e:
                    print(e)
                    pass
        # 预约成功
        if(isBooked):
            # 由于返回的参数是list类型，修改后的res才是dict类型
            res = getReservations(token)[0]
            message = "{}\n{}--{}\n{}".format(res['receipt'],res['begin'],res['end'],res['location'])
            print(message)
        else:
            message = '-1。\n预约失败！！！'
    else:
        message = '-1。\n登录出现问题！！！'
    # 将相关信息发送到手机
    params = ['zfb',message]
    print('----\n'+message)
    #sendSMS(config.PHONE_NUMBER,params)
    #getHistory(1,token)
    

