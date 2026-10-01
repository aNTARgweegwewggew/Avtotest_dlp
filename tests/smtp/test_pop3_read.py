import pytest

from src.smtp.read_mail_pop3 import (
    connect_pop3,
    read_email_by_uuid,
)
from src.smtp.send_mail import send_email


@pytest.mark.parametrize(
    "smtp_port, pop3_port",
    [
        (25, 110),
        (25, 995),

        (587, 110),
        (587, 995),

        pytest.param(
            465,
            110,
            marks=pytest.mark.xfail(
                reason="На Romeo отсутствует SMTP + SSL"
            ),
        ),

        pytest.param(
            465,
            995,
            marks=pytest.mark.xfail(
                reason="На Romeo отсутствует SMTP + SSL"
            ),
        ),
    ],
)
def test_pop3_read(
    mailbox,
    smtp_port,
    pop3_port,
):

    uuid = send_email(smtp_port)

    server = connect_pop3(pop3_port)

    try:
        found = read_email_by_uuid(
            server,
            uuid,
        )
    finally:
        server.quit()

    assert found is not None

    body = found.get_body(
        preferencelist=("plain",)
    )

    assert body is not None

    text = body.get_content()

    assert text.strip() == (
        f"Отправка текста test #{uuid}"
    )

