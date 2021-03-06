#/bin/env python
# -*- coding: utf-8 -*-

from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
import smtplib


def sendEmail(photos, status, title=u'交易状态'):
    msg = MIMEMultipart()
    msg['From'] = "tianbin6961@sina.com"
    msg['To'] = "tianbin696@163.com"
    msg['Subject'] = Header(title, 'utf-8').encode()

    # 邮件正文是MIMEText:
    msg.attach(MIMEText("%s" % status, 'plain', 'utf-8'))

    # 添加附件就是加上一个MIMEBase，从本地读取一个图片:
    for photo in photos:
        with open(photo, 'rb') as f:
            # 设置附件的MIME和文件名，这里是png类型:
            mime = MIMEBase('image', 'png', filename=photo)
            # 加上必要的头信息:
            mime.add_header('Content-Disposition', 'attachment', filename=photo)
            mime.add_header('Content-ID', '<0>')
            mime.add_header('X-Attachment-Id', '0')
            # 把附件的内容读进来:
            mime.set_payload(f.read())
            # 用Base64编码:
            encoders.encode_base64(mime)
            # 添加到MIMEMultipart:
            msg.attach(mime)
    server = smtplib.SMTP()
    server.connect("smtp.sina.com")
    server.login("tianbin6961@sina.com", "tianbin6961994")
    server.sendmail("tianbin6961@sina.com", "tianbin696@163.com", msg.as_string())
    server.quit()

if __name__ == "__main__":
    sendEmail(['auto_deal.png'],'test')
