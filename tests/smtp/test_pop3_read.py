"""Проверки получения отправленных писем через POP3 и POP3S."""

import pytest

from src.smtp.config import POP3_TEST_PORTS, SMTP_TEST_PORTS
from src.smtp.send_mail import send_email


@pytest.mark.parametrize(
    ("smtp_port", "pop3_port"),
    [
        (smtp_port, pop3_port)
        for smtp_port in SMTP_TEST_PORTS
        for pop3_port in POP3_TEST_PORTS
    ],
)
def test_pop3_read(smtp_port, pop3_port, find_received_email):
    """Отправить письмо и проверить его текст при чтении через POP3."""
    unique_id = send_email(smtp_port)
    message = find_received_email("pop3", pop3_port, unique_id)

    assert message is not None
    body = message.get_body(preferencelist=("plain",))
    assert body is not None
    assert body.get_content().strip() == (
        f"Отправка текста test #{unique_id}"
    )
