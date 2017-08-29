# -*- coding:utf-8 -*-

import getopt
import sys
import ConfigParser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

config_file = "emailset.ini"
attfiles =""

opts, args = getopt.getopt(sys.argv[1:], "p:f:")
for o, v in opts:
    if o == "-p":
        config_file = v
    elif o == "-f":
        attfiles = v

config = ConfigParser.ConfigParser()
config.readfp(open(config_file, "rb"))
Email_host = config.get("Email", "host")
Email_port = config.get("Email", "port")
Email_user = config.get("Email", "user")
Email_pass = config.get("Email", "pass")
Email_from = config.get("Email", "from")
to_list = config.get("Email", "to_list")
Email_subject = config.get("Email", "subject")
Email_text = config.get("Email", "text")

Email_to_list=[]
for Email_to in to_list.split(','):
    Email_to_list.append(Email_to)

msg = MIMEMultipart()
msg['Subject'] =  Email_subject
msg.attach(MIMEText(Email_text, 'plain', 'gbk')) #utf-8

for fs in attfiles.split(','):
    att = MIMEText(open(r'%s' % fs, 'rb').read(), 'base64', 'utf-8')  # 添加附件
    att["Content-Type"] = 'application/octet-stream'
    att["Content-Disposition"] = 'attachment; filename="%s"' % fs
    msg.attach(att)

try:
    s = smtplib.SMTP_SSL()  # smtplib.SMTP() 如果是使用SSL端口:SMTP_SSL
    s.connect(Email_host,Email_port)
    s.login(Email_user,Email_pass)
    s.sendmail(Email_from,Email_to_list, msg.as_string())
except Exception, e:
    print str(e)
finally:
    s.close()