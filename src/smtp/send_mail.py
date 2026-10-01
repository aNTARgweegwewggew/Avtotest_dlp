import os
import smtplib
import uuid

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.smtp.config import (
    MAIL_HOST,
    MAIL_USERNAME,
    MAIL_PASSWORD,
)


def send_email(port, attachment=None):

    unique_id = str(uuid.uuid4())[:8]

    email_body = f"Отправка текста test #{unique_id}"

    msg = MIMEMultipart()
    msg["Subject"] = "DLP INCIDENT"
    msg["From"] = "isaft@tst.local"
    msg["To"] = "isafr@tst.local"

    msg.attach(
        MIMEText(
            email_body,
            "plain",
        )
    )

    # Если передали папку — прикладываем все файлы из неё
    if attachment:

        if not os.path.isdir(attachment):
            raise FileNotFoundError(
                f"Папка не найдена: {attachment}"
            )

        for filename in os.listdir(attachment):

            file_path = os.path.join(
                attachment,
                filename,
            )

            if not os.path.isfile(file_path):
                continue

            with open(file_path, "rb") as file:

                part = MIMEBase(
                    "application",
                    "octet-stream",
                )

                part.set_payload(
                    file.read()
                )

                encoders.encode_base64(part)

                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{filename}"',
                )

                msg.attach(part)

                print(
                    f"Приложен файл: {filename}"
                )

    if port == 465:

        server = smtplib.SMTP_SSL(
            MAIL_HOST,
            port,
        )

    elif port == 587:

        server = smtplib.SMTP(
            MAIL_HOST,
            port,
        )

        server.starttls()

        server.login(
            MAIL_USERNAME,
            MAIL_PASSWORD,
        )

    else:

        server = smtplib.SMTP(
            MAIL_HOST,
            port,
        )

    with server:

        server.send_message(msg)

    print(
        f"Отправлено сообщение с ID: {unique_id}"
    )

    return unique_id