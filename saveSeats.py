#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: 'zfb'
# time: 18-09-13 22:55:35
import json
import requests
import datetime
import time

import config
import SQLHelper
from reserveSeat import login, getRoomsInfo, saveSeatsInfoOfRoom
from log import initLog

if __name__ == '__main__':
    logging = initLog('save.log','reserve')
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
    except Exception as e:
        print(e)
