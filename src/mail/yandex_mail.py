"""Отправка тестовых писем через SMTP Яндекса с OAuth-токеном."""

import logging
import os
import smtplib
import uuid
from collections.abc import Iterable
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from src.smtp.send_mail import build_test_email_body


logger = logging.getLogger(__name__)
SUPPORTED_PORTS = {465, 587}


def _get_mail_settings():
    """Прочитать отдельные настройки SMTP Яндекс.Почты из переменных окружения."""
    settings = {
        "host": os.getenv("YANDEX_MAIL_HOST", "smtp.yandex.com"),
        "port": int(os.getenv("YANDEX_MAIL_PORT", "465")),
        "username": os.getenv("YANDEX_MAIL_USERNAME", ""),
        "sender": os.getenv("YANDEX_MAIL_FROM")
        or os.getenv("YANDEX_MAIL_USERNAME", ""),
        "recipient": os.getenv("YANDEX_MAIL_TO", ""),
    }
    missing = [
        name
        for name in ("username", "recipient")
        if not settings[name]
    ]
    if missing:
        variable_names = {
            "username": "YANDEX_MAIL_USERNAME",
            "recipient": "YANDEX_MAIL_TO",
        }
        raise RuntimeError(
            "Для тестов Яндекс.Почты задайте: "
            + ", ".join(variable_names[name] for name in missing)
        )
    if settings["port"] not in SUPPORTED_PORTS:
        raise RuntimeError(
            "YANDEX_MAIL_PORT должен быть 465 (SSL) или 587 (STARTTLS)"
        )
    return settings


def build_yandex_test_email(
    unique_id,
    attachment_paths: Iterable[str | Path] = (),
):
    """Собрать MIME-письмо с DLP-маркером и файлами.

    unique_id попадает в тему и текст, чтобы найти письмо в базе DLP.
    attachment_paths перечисляет файлы, которые нужно добавить к письму.
    """
    settings = _get_mail_settings()
    message = MIMEMultipart()
    message["Subject"] = f"DLP AUTOTEST YANDEX {unique_id}"
    message["From"] = settings["sender"]
    message["To"] = settings["recipient"]
    message.attach(
        MIMEText(
            build_test_email_body(unique_id, include_dlp_marker=True),
            "plain",
            "utf-8",
        )
    )

    for attachment_path in attachment_paths:
        path = Path(attachment_path)
        if not path.is_file():
            raise FileNotFoundError(f"Не найден файл-вложение: {path}")

        part = MIMEBase("application", "octet-stream")
        part.set_payload(path.read_bytes())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{path.name}"',
        )
        message.attach(part)

    return message


def send_yandex_test_email(
    access_token,
    attachment_paths: Iterable[str | Path] = (),
):
    """Отправить письмо через SMTP Яндекса с OAuth XOAUTH2.

    access_token используется только для авторизации, пароль почты не нужен.
    attachment_paths перечисляет ноль, один или несколько файлов для отправки.
    Возвращает уникальный ID, включённый в тему и текст письма.
    """
    settings = _get_mail_settings()
    attachment_paths = tuple(attachment_paths)
    unique_id = uuid.uuid4().hex[:12]
    message = build_yandex_test_email(unique_id, attachment_paths)
    auth_payload = (
        f"user={settings['username']}\x01"
        f"auth=Bearer {access_token}\x01\x01"
    )

    if settings["port"] == 465:
        server = smtplib.SMTP_SSL(settings["host"], settings["port"], timeout=30)
    else:
        server = smtplib.SMTP(settings["host"], settings["port"], timeout=30)

    with server:
        if settings["port"] == 587:
            server.starttls()
            server.ehlo()
        server.auth("XOAUTH2", lambda _challenge: auth_payload)
        server.send_message(message)

    logger.info(
        "Яндекс.Почта приняла тестовое письмо %s с вложениями: %s",
        unique_id,
        len(attachment_paths),
    )
    return unique_id
