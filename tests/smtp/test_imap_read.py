"""Проверки получения отправленных писем через IMAP и IMAPS."""

import pytest

from src.smtp.config import IMAP_TEST_PORTS, SMTP_TEST_PORTS
from src.smtp.send_mail import send_email


pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("smtp_port", "imap_port"),
    [
        (smtp_port, imap_port)
        for smtp_port in SMTP_TEST_PORTS
        for imap_port in IMAP_TEST_PORTS
    ],
)
def test_imap_read(smtp_port, imap_port, find_received_email):
    """Отправить письмо и проверить его текст при чтении через IMAP."""
    unique_id = send_email(smtp_port)
    message = find_received_email("imap", imap_port, unique_id)

    assert message is not None
    body = message.get_body(preferencelist=("plain",))
    assert body is not None
    assert body.get_content().strip() == (
        f"Отправка текста test #{unique_id}"
    )
