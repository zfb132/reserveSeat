#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: 'zfb'
# time: 18-09-13 22:55:35
from qcloudsms_py import SmsSingleSender
from qcloudsms_py.httpclient import HTTPError
import config
import json
import requests

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
    #print(result.text)
    status = json.loads(result.text)['status']
    if(status == 'success'):
        token = json.loads(result.text)['data']['token']
        #print(token)
        return status,token
    else:
        print(json.loads(result.text)['message'])
        exit(1)
    
if __name__ == '__main__':
    params=['zfb','666。图书馆预约座位成功，时间是2018年9月14日早上八点半到晚上十点，请不要迟到！！！']
    #sendSMS(config.PHONE_NUMBER,params)
    print(login(config.USER,config.PASSWORD))
