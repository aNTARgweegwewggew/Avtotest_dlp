"""Подключение к IMAP и поиск тестовых писем по уникальному маркеру."""

import logging
import imaplib
from email import policy
from email.parser import BytesParser

from src.smtp.config import (
    MAIL_HOST,
    MAIL_USERNAME,
    MAIL_PASSWORD,
    MAIL_TIMEOUT_SECONDS,
    validate_mail_config,
)


logger = logging.getLogger(__name__)


def connect_imap(port):
    """Подключиться и выполнить вход в настроенный IMAP- или IMAPS-сервис."""
    validate_mail_config()
    if port == 993:
        server = imaplib.IMAP4_SSL(
            MAIL_HOST,
            port,
            timeout=MAIL_TIMEOUT_SECONDS,
        )
    else:
        server = imaplib.IMAP4(
            MAIL_HOST,
            port,
            timeout=MAIL_TIMEOUT_SECONDS,
        )

    server.login(
        MAIL_USERNAME,
        MAIL_PASSWORD,
    )

    server.select("INBOX")

    return server


def read_email_by_uuid(server, uuid):
    """Найти первое IMAP-письмо, в тексте которого есть ID теста."""
    status, data = server.uid(
        "search",
        None,
        "ALL",
    )

    if status != "OK":
        raise RuntimeError(f"IMAP search failed with status {status}")

    message_ids = data[0].split()

    for message_id in reversed(message_ids):

        status, data = server.uid(
            "fetch",
            message_id,
            "(BODY.PEEK[])",
        )

        if status != "OK":
            continue

        raw_email = None

        for item in data:
            if isinstance(item, tuple):
                raw_email = item[1]
                break

        if not raw_email:
            continue

        mail = BytesParser(
            policy=policy.default
        ).parsebytes(raw_email)

        body = mail.get_body(
            preferencelist=("plain",)
        )

        if not body:
            continue

        text = body.get_content()

        if uuid in text:
            logger.info("Found test message %s via IMAP", uuid)
            return mail

    return None