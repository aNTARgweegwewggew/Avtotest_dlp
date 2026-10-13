"""Подключение к POP3 и поиск тестовых писем по уникальному маркеру."""

import logging
import poplib
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


def connect_pop3(port):
    """Подключиться и выполнить вход в настроенный POP3- или POP3S-сервис."""
    validate_mail_config()
    if port == 995:
        server = poplib.POP3_SSL(
            MAIL_HOST,
            port,
            timeout=MAIL_TIMEOUT_SECONDS,
        )
    else:
        server = poplib.POP3(
            MAIL_HOST,
            port,
            timeout=MAIL_TIMEOUT_SECONDS,
        )

    server.user(MAIL_USERNAME)
    server.pass_(MAIL_PASSWORD)

    return server


def read_email_by_uuid(server, uuid):
    """Найти первое POP3-письмо, в тексте которого есть ID теста."""
    messages = len(server.list()[1])
    logger.info("Searching %s POP3 messages for test ID %s", messages, uuid)

    for message_number in range(messages, 0, -1):

        _, lines, _ = server.retr(message_number)

        raw_email = b"\r\n".join(lines)

        mail = BytesParser(
            policy=policy.default
        ).parsebytes(raw_email)

        body = mail.get_body(
            preferencelist=("plain",)
        )

        if body:
            text = body.get_content()
            if uuid in text:
                logger.info("Found test message %s via POP3", uuid)
                return mail

    return None
