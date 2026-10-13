"""Проверки количества и наличия вложений в полученных письмах."""

from pathlib import Path

import pytest

from src.smtp.config import IMAP_TEST_PORTS, POP3_TEST_PORTS, SMTP_TEST_PORTS
from src.smtp.send_mail import send_email


TEST_DATA = Path(__file__).resolve().parents[1] / "data" / "mail"
SINGLE_ATTACHMENT_FOLDER = TEST_DATA / "single"
MULTIPLE_ATTACHMENTS_FOLDER = TEST_DATA / "multiple"

RECEIVE_COMBINATIONS = [
    (smtp_port, protocol, receive_port)
    for smtp_port in SMTP_TEST_PORTS
    for protocol, ports in (
        ("pop3", POP3_TEST_PORTS),
        ("imap", IMAP_TEST_PORTS),
    )
    for receive_port in ports
]


def _assert_test_message(message, unique_id):
    """Проверить, что найдено письмо с ожидаемым текстом и ID теста."""
    assert message is not None
    body = message.get_body(preferencelist=("plain",))
    assert body is not None
    assert body.get_content().strip() == (
        f"Отправка текста test #{unique_id}"
    )


def _attachment_names(message):
    """Вернуть имена MIME-частей, отмеченных как вложения."""
    return [
        part.get_filename()
        for part in message.walk()
        if part.get_content_disposition() == "attachment"
    ]


@pytest.mark.parametrize(
    ("smtp_port", "protocol", "receive_port"),
    RECEIVE_COMBINATIONS,
)
@pytest.mark.parametrize(
    ("folder", "expected_count"),
    [
        (SINGLE_ATTACHMENT_FOLDER, 1),
        (MULTIPLE_ATTACHMENTS_FOLDER, 2),
    ],
)
def test_email_attachments(
    smtp_port,
    protocol,
    receive_port,
    folder,
    expected_count,
    find_received_email,
):
    """Отправить письмо с вложениями и проверить их количество после получения."""
    unique_id = send_email(smtp_port, folder)
    message = find_received_email(protocol, receive_port, unique_id)
    _assert_test_message(message, unique_id)

    attachment_names = _attachment_names(message)
    assert len(attachment_names) == expected_count
    assert all(attachment_names)
