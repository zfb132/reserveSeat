# 图书馆预约座位
## 准备工作
1. 基于Python3编写，因此需要首先安装Python3
2. 依赖放在requirements.txt中，运行前需要先安装依赖的库  
`pip install -r requirements.txt`
3. 重命名`config.example.py`为`config.py`，修改里面的个人配置，注意自己申请腾讯云短信应用
## 运行程序
开始预约，系统会自动预约指定房间（可以多个）的空闲座位，打开终端切换到当前目录并输入：  
`python3 reserve.py`  
失败则退出，成功会发送短信通知
## 全自动化
使用Linux系统的定时任务`crontab`来实现（也可以自己用Windows实现），在终端编辑定时文件：  
`crontab -e`  
在打开的文件中添加一行内容：  
`44 22 * * * /usr/bin/python3 ~/reserveSeat/reserve.py`  
这句话意思是：每天的22:45分开始运行本程序（假设本程序位于主目录下，根据实际位置自行更改`py`文件路径）
## 其他信息
保存所有座位信息到数据库：  
`python3 saveSeats.py`  
## API相关
获取所有自习室的接口又改变了：  
~~`/rest/v2/free/filters?token={}`~~ -> `/rest/v2/room/stats2/0?token=`  
获取某个图书馆内的自习室的接口也改变了：  
~~`/rest/v2/room/layoutByDate/{}/{}?token={}`~~ -> `/rest/v2/room/stats2/{}?token=`