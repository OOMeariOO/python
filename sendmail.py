# -*- coding: UTF-8 -*-

# @Author: 米 雷
# @File: sendmail.py
# @Time: 2017/5/26
# @Contact: 1262585769@qq.com
# @Description: 发送一个带附件的邮件

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

smtpServer = '********'
sender = '********'
receivers = ['1262585769@qq.com', '********@sina.cn']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
                                                          #这里是一个list，可以发送多人。。。

# 创建一个带附件的实例
message = MIMEMultipart()
message['From'] = Header("米雷", 'utf-8')
message['To'] = Header("测试", 'utf-8')
subject = 'title'# 这里是邮件的标题
message['Subject'] = Header(subject, 'utf-8')

# 邮件正文内容
message.attach(MIMEText('这是Python 邮件发送测试……', 'plain', 'utf-8'))

# 构造附件1，传送当前目录下的 test.txt 文件
att1 = MIMEText(open('test.txt' , 'rb').read(), 'base64', 'utf-8')
att1["Content-Type"] = 'application/octet-stream'
# 这里的filename可以任意写，写什么名字，邮件中显示什么名字
att1["Content-Disposition"] = 'attachment; filename="test.txt"'
message.attach(att1)

try:
    smtpObj = smtplib.SMTP('********.com', 25)
    smtpObj.login('********.com', '********')
    smtpObj.sendmail(sender, receivers, message.as_string())
    print "邮件发送成功"
except smtplib.SMTPException:
    print "Error: 无法发送邮件"
