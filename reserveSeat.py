#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: 'zfb'
# time: 18-10-29 23:08:14
from qcloudsms_py import SmsSingleSender
from qcloudsms_py.httpclient import HTTPError
import pymysql

import json
import requests
import ssl
import datetime
import time
import random
import logging

import config
import SQLHelper
#代码页加入以下这个
from requests.packages.urllib3.exceptions import InsecureRequestWarning
# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging = logging.getLogger('reserve.reserveSeat')

# 报头
headers = {
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 ",
    'Host':"seat.lib.whu.edu.cn:8443"
}

# 预约系统网址
url_base = config.URL_BASE

# 向某个指定号码发送特定内容的消息
def sendSMS(number,params):
    ssender = SmsSingleSender(config.APPID, config.APPKEY)
    try:
        result = ssender.send_with_param(86, number, config.TEMPLATE_ID, 
                params, sign=config.SMS_SIGN, extend="", ext="")
    except HTTPError as e:
        log = json.dumps(e, ensure_ascii=False)
        logging.error(log)
        print(log)
    except Exception as e:
        log = json.dumps(e, ensure_ascii=False)
        logging.error(log)
        print(log)
    log = json.dumps(result, ensure_ascii=False)
    logging.debug(log)
    print(log)
    
# 登录预约系统
def login(user,pwd):
    url = url_base + "/rest/auth?username={}&password={}".format(user,pwd)
    logging.debug(url)
    result = requests.get(url, headers=headers, verify=False)
    logging.debug('result:'+result.text)
    status = json.loads(result.text)['status']
    if(status == 'success'):
        token = json.loads(result.text)['data']['token']
        logging.debug(token)
        print(token)
        return token
    else:
        log = '登录异常：'+json.loads(result.text)['message']
        logging.error(log)
        raise Exception(log)
        
# 获得预约历史记录
# offset从1开始，每次获取10条记录
def getHistory(offset,token):
    url = url_base + "/rest/v2/history/{}/10?token={}".format(offset,token)
    logging.debug(url)
    result = requests.get(url, headers=headers)
    logging.debug('result:'+result.text)
    status = json.loads(result.text)['status']
    if(status == 'success'):
        history = json.loads(result.text)['data']['reservations']
        return history
    else:
        log = '查询历史记录异常：'+json.loads(result.text)['message']
        logging.error(log)
        raise Exception(log)

# 获取当前预约信息
def getReservations(token):
    url = url_base + "/rest/v2/user/reservations?token={}".format(token)
    logging.debug(url)
    result = requests.get(url, headers=headers,verify=False)
    logging.debug('result:'+result.text)
    status = json.loads(result.text)['status']
    if(status == 'success'):
        reservations = json.loads(result.text)['data']
        return reservations
    else:
        log = '获取预约信息异常：'+json.loads(result.text)['message']
        logging.error(log)
        raise Exception(log)
        
# 获取房间楼层信息
def getRoomsInfo(token):
    url = url_base + "/rest/v2/free/filters?token={}".format(token)
    logging.debug(url)
    result = requests.get(url, headers=headers, verify=False)
    logging.debug('result:'+result.text)
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
        log = '获取房间信息异常：'+json.loads(result.text)['message']
        logging.error(log)
        raise Exception(log)


def bookSeat(token,seat,date,stime=config.STIME,etime=config.ETIME):
    url = url_base + "/rest/v2/freeBook"
    bookParams={
        "startTime": str(stime),
        "endTime": str(etime),
        "seat": int(seat),
        "date": str(date),
        "t": "1",
        "t2": "2"
    }
    #token=urllib.parse.urlencode(bookParams)
    print(bookParams)
    myheader={
        'Host': 'seat.lib.whu.edu.cn:8443',
        'Accept-Language': 'zh-cn', 
        'Accept-Encoding': 'gzip, deflate', 
        'Accept': '*/*', 
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 
        'Connection': 'keep-alive', 
        'token': str(token), 
        'User-Agent': 'doSingle/11 CFNetwork/893.14.2 Darwin/17.3.0'
    }
    logging.debug(url)
    logging.debug(bookParams)
    logging.debug(myheader)
    result = requests.post(url=url, headers=myheader, data=bookParams, verify=False)
    logging.debug('result:'+result.text)
    print(result.text)
    status = json.loads(result.text)['status']
    if(status == 'success'):
        return [True,json.loads(result.text)['data']]
    else:
        log = '预约出现异常：'+json.loads(result.text)['message']
        logging.error(log)
        #raise Exception(log)

# 预约指定座位        
def reserveSeat(token,seat,date,stime=config.STIME,etime=config.ETIME):
    url = url_base + "/rest/v2/freeBook"
    bookParams = {}
    bookParams['token'] = token
    bookParams['seat'] = seat
    bookParams['date'] = date
    bookParams['startTime'] = stime
    bookParams['endTime'] = etime
    logging.debug(url)
    logging.debug(bookParams)
    ssl._create_default_https_context=ssl._create_unverified_context
    result = requests.post(url, params=bookParams, headers=headers,verify =False)
    logging.debug('result:'+result.text)
    print(result.text)
    status = json.loads(result.text)['status']
    if(status == 'success'):
        return [True,json.loads(result.text)['data']]
    else:
        log = '预约出现异常：'+json.loads(result.text)['message']
        logging.error(log)
        #raise Exception(log)

# 取消指定id的预约
def cancelSeat(token,id):
    url = url_base + "/rest/v2/cancel/{}?token={}".format(id,token)
    logging.debug(url)
    result = requests.get(url, headers=headers)
    logging.debug('result:'+result.text)
    status = json.loads(result.text)['status']
    if(status == 'success'):
        return True
    else:
        log = '取消预约异常：'+json.loads(result.text)['message']
        logging.error(log)
        raise Exception(log)

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
        logging.debug(url)
        logging.debug(searchParams)
        result = requests.post(url,params=searchParams,headers=headers,verify=False)
        logging.debug('result:'+result.text)
        status = json.loads(result.text)['status']
        if(status == True):
            data = json.loads(result.text)['data']['seats']
            # 若无空闲座位则进行下一个房间
            if(len(data)<1):
                log = '房间{}无空闲座位'.format(room)
                logging.debug(log)
                print(log)
                continue
            for k in data:
                seat = data[k]
                seatIDs.append(seat['id'])
        else:
            logging.error('搜索出错！')
            print('搜索出错！')
    logging.debug(seatIDs)
    print(seatIDs)
    return seatIDs

# 存储某个房间内当前所有座位信息
def saveSeatsInfoOfRoom(id,date,token,roomInfo):
    log = '正在获取位于{}{}楼的{}的座位信息'.format(roomInfo[1],roomInfo[2],roomInfo[0])
    logging.debug(log)
    print(log,id)
    url = url_base + "/rest/v2/room/layoutByDate/{}/{}?token={}".format(id,date,token)
    #url = url_base + "/rest/v2/room/layoutByDate/{}/{}".format(id,date)
    result = requests.get(url, headers=headers, verify=False)
    logging.debug('result:'+result.text)
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
                        logging.error(str(seat)+'\n'+str(roomInfo)+repr(e))
                        print(str(seat)+'\n'+str(roomInfo))
                        print(repr(e))
            # 必须有这一句
            cursor.execute("commit")
            cursor.close()
            db.close()
        except Exception as e:
            logging.error(repr(e))
            print(repr(e))
    else:
        log = '获取座位信息异常：'+json.loads(result.text)['message']
        logging.error(log)
        raise Exception(log)

