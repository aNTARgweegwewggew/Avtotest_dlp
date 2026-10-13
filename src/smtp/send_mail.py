"""Формирование и отправка тестовых писем через настроенный SMTP-сервер."""

import logging
import smtplib
import uuid
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from src.smtp.config import (
    MAIL_FROM,
    MAIL_HOST,
    MAIL_PASSWORD,
    MAIL_TIMEOUT_SECONDS,
    MAIL_TO,
    MAIL_USERNAME,
    validate_mail_config,
)


logger = logging.getLogger(__name__)
DLP_TEST_MARKER = "secret password"


def build_test_email_body(unique_id, include_dlp_marker=False):
    """Собрать текст письма с ID теста и необязательным DLP-маркером."""
    body = f"Отправка текста test #{unique_id}"
    if include_dlp_marker:
        return f"{DLP_TEST_MARKER}\n{body}"
    return body


def send_email(port, attachment=None, include_dlp_marker=False):
    """Отправить тестовое письмо и вернуть его уникальный ID."""
    validate_mail_config()
    unique_id = uuid.uuid4().hex[:12]
    email_body = build_test_email_body(
        unique_id,
        include_dlp_marker=include_dlp_marker,
    )

    message = MIMEMultipart()
    message["Subject"] = f"DLP AUTOTEST {unique_id}"
    message["From"] = MAIL_FROM
    message["To"] = MAIL_TO
    message.attach(MIMEText(email_body, "plain", "utf-8"))

    if attachment is not None:
        attachment_dir = Path(attachment)
        if not attachment_dir.is_dir():
            raise FileNotFoundError(f"Attachment directory does not exist: {attachment_dir}")

        files = sorted(path for path in attachment_dir.rglob("*") if path.is_file())
        if not files:
            raise FileNotFoundError(f"Attachment directory contains no files: {attachment_dir}")

        for file_path in files:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(file_path.read_bytes())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{file_path.name}"',
            )
            message.attach(part)

        logger.info(
            "Sending test email %s with %s attachment(s) over SMTP port %s",
            unique_id,
            len(files),
            port,
        )
    else:
        logger.info(
            "Sending test email %s over SMTP port %s",
            unique_id,
            port,
        )

    if port == 465:
        server = smtplib.SMTP_SSL(
            MAIL_HOST,
            port,
            timeout=MAIL_TIMEOUT_SECONDS,
        )
    else:
        server = smtplib.SMTP(
            MAIL_HOST,
            port,
            timeout=MAIL_TIMEOUT_SECONDS,
        )

    with server:
        if port == 587:
            server.starttls()
        if port != 25:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(message)

    logger.info("Test email %s accepted by SMTP server", unique_id)
    return unique_id
