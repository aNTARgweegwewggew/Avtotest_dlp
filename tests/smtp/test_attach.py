import pytest

from src.smtp.send_mail import send_email

from src.smtp.read_mail_pop3 import (
    connect_pop3,
    read_email_by_uuid as read_pop3_email_by_uuid,
)

from src.smtp.read_mail_imap import (
    connect_imap,
    read_email_by_uuid as read_imap_email_by_uuid,
)


SINGLE_ATTACHMENT_FOLDER = "/home/user/test_yandex/single"

MULTIPLE_ATTACHMENTS_FOLDER = "/home/user/test_yandex/multiple"


SMTP_COMBINATIONS = [
    # SMTP 25
    (25, "pop3", 110),
    (25, "pop3", 995),
    (25, "imap", 143),
    (25, "imap", 993),

    # SMTP 587 + STARTTLS
    (587, "pop3", 110),
    (587, "pop3", 995),
    (587, "imap", 143),
    (587, "imap", 993),

    # SMTP 465 + SSL
    pytest.param(
        465,
        "pop3",
        110,
        marks=pytest.mark.xfail(
            reason="На текущем почтовом сервере отсутствует SMTP + SSL"
        ),
    ),
    pytest.param(
        465,
        "pop3",
        995,
        marks=pytest.mark.xfail(
            reason="На текущем почтовом сервере отсутствует SMTP + SSL"
        ),
    ),
    pytest.param(
        465,
        "imap",
        143,
        marks=pytest.mark.xfail(
            reason="На текущем почтовом сервере отсутствует SMTP + SSL"
        ),
    ),
    pytest.param(
        465,
        "imap",
        993,
        marks=pytest.mark.xfail(
            reason="На текущем почтовом сервере отсутствует SMTP + SSL"
        ),
    ),
]


def receive_email(
    protocol,
    receive_port,
    unique_id,
):
    if protocol == "pop3":

        server = connect_pop3(
            receive_port
        )

        try:
            return read_pop3_email_by_uuid(
                server,
                unique_id,
            )
        finally:
            server.quit()

    server = connect_imap(
        receive_port
    )

    try:
        return read_imap_email_by_uuid(
            server,
            unique_id,
        )
    finally:
        server.logout()


def check_email(
    found,
    unique_id,
):
    assert found is not None

    body = found.get_body(
        preferencelist=("plain",)
    )

    assert body is not None

    text = body.get_content()

    assert text.strip() == (
        f"Отправка текста test #{unique_id}"
    )


def get_attachments(found):
    return [
        part
        for part in found.walk()
        if part.get_content_disposition() == "attachment"
    ]


@pytest.mark.parametrize(
    "smtp_port, protocol, receive_port",
    SMTP_COMBINATIONS,
)
def test_one_attachment(
    mailbox,
    smtp_port,
    protocol,
    receive_port,
):
    unique_id = send_email(
        smtp_port,
        SINGLE_ATTACHMENT_FOLDER,
    )

    found = receive_email(
        protocol,
        receive_port,
        unique_id,
    )

    check_email(
        found,
        unique_id,
    )

    attachments = get_attachments(
        found
    )

    assert len(attachments) == 1


@pytest.mark.parametrize(
    "smtp_port, protocol, receive_port",
    SMTP_COMBINATIONS,
)
def test_multiple_attachments(
    mailbox,
    smtp_port,
    protocol,
    receive_port,
):
    unique_id = send_email(
        smtp_port,
        MULTIPLE_ATTACHMENTS_FOLDER,
    )

    found = receive_email(
        protocol,
        receive_port,
        unique_id,
    )

    check_email(
        found,
        unique_id,
    )

    attachments = get_attachments(
        found
    )

    assert len(attachments) > 1