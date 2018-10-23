#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: 'zfb'
# time: 18-09-13 22:55:35
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
# 预约系统网址
url_base = "http://seat.lib.whu.edu.cn"

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
                if(len(seat)>2):                    # 开始座位信息插入到数据库
                    try:
                        cursor.execute(
                            "insert into seat values ({},'{}','{}','{}','{}',{},{},{},{},{},'{}',{},'{}')".format(
                        seat['id'],seat['name'],k,seat['type'],seat['status'],seat['window'],
                        seat['power'],seat['computer'],seat['local'],roomInfo[2],roomInfo[0],roomInfo[3],roomInfo[1]))
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

if __name__ == '__main__':
    SQLHelper.initDataBase()
    SQLHelper.initTable()
    # 登录预约系统
    try:
        token = login(config.USER,config.PASSWORD)
        # 获取及写入座位信息
        rooms = getRoomsInfo(token)
        dateToday = str(datetime.date.today())
        for room in rooms:
            rooms[room].append(room)
            saveSeatsInfoOfRoom(room, dateToday, token, rooms[room])
        print('成功获取座位信息')
    except Exception as e:                                                 print(e)
