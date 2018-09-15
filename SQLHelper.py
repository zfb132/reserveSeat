#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: 'zfb'
# time: 18-09-14 17:35:12
import pymysql
import config


def initDataBase():
    try:
        db = pymysql.connect(host='localhost',user='root', password=config.SQLPWD, port=3306)
        cursor = db.cursor()
        # 先删除原有数据库，防止插入时产生冲突
        cursor.execute("drop database if exists {}".format(config.DBNAME))
        cursor.execute(
            "create database if not exists {} default character set utf8".format(config.DBNAME))
        cursor.close()
        db.close()
    except Exception as e:
        print(e)
        
def initTable():
    try:
        db = pymysql.connect(host='localhost',user='root', 
            password=config.SQLPWD, db=config.DBNAME, port=3306, charset='utf8')
        cursor = db.cursor()
        # status字段意义不大，变化太快
        sql = 'create table if not exists seat(\
                id int(20) not null,\
                name varchar(10) default null,\
                type varchar(20) default null,\
                status varchar(20) default null,\
                window boolean,\
                power boolean,\
                computer boolean,\
                local boolean,\
                floor int(5),\
                room varchar(40) default null,\
                roomId int(5), \
                building varchar(10),\
                primary key(id)\
            )engine=InnoDB default charset=utf8'
        cursor.execute(sql)
        cursor.close()
        db.close()
    except Exception as e:
        print(e)
        

