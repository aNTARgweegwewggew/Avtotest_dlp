import pytest

from src.smtp.send_mail import send_email
from src.smtp.read_mail_imap import (
    connect_imap,
    read_email_by_uuid,
)


@pytest.mark.parametrize(
    "smtp_port, imap_port",
    [
        (25, 143),
        (25, 993),

        (587, 143),
        (587, 993),

        pytest.param(
            465,
            143,
            marks=pytest.mark.xfail(
                reason="На Romeo отсутствует SMTP + SSL"
            ),
        ),

        pytest.param(
            465,
            993,
            marks=pytest.mark.xfail(
                reason="На Romeo отсутствует SMTP + SSL"
            ),
        ),
    ],
)
def test_smtp_imap(
    mailbox,
    smtp_port,
    imap_port,
):

    uuid = send_email(smtp_port)

    server = connect_imap(imap_port)

    try:
        found = read_email_by_uuid(
            server,
            uuid,
        )
    finally:
        server.logout()

    assert found is not None

    body = found.get_body(
        preferencelist=("plain",)
    )

    assert body is not None

    text = body.get_content()

    assert text.strip() == (
        f"Отправка текста test #{uuid}"
    )