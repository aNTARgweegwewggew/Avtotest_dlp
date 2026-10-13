"""Вспомогательная отправка писем с произвольным текстом и вложениями."""

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import smtplib

def send_email(email_body,email_subject,email_from,email_to,smtp_ip,attachment = None):
    """Отправить письмо через SMTP и вернуть результат отправки."""
    msg = MIMEMultipart()
    msg["Subject"] = email_subject
    msg["From"] = email_from
    msg["To"] = email_to

    msg.attach(MIMEText(email_body,"plain"))

    if attachment:
        for file_path in attachment:
            if not os.path.isfile(file_path):
                print(f"Файл не найден - {file_path}")
                continue
            try:
                with open(file_path,"rb") as file:
                    part = MIMEBase ("application","octet-stream")
                    part.set_payload(file.read())
                    encoders.encode_base64(part)
                    filename=os.path.basename(file_path)
                    part.add_header("Content-Disposition",f'attachment; filename="{filename}"')

                    msg.attach(part)

                    print(f'Приложен файл: {filename}')

            except Exception as e:
                print(f"Ошибка при вложении {file_path} : {e}")

    with smtplib.SMTP(smtp_ip,25) as server:
        server.send_message(msg)
        print(f"Отправлено сообщение")

    return True
