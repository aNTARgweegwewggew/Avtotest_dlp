import poplib
from email import policy
from email.parser import BytesParser

from src.smtp.config import (
    MAIL_HOST,
    MAIL_USERNAME,
    MAIL_PASSWORD,
)


def connect_pop3(port):

    if port == 995:
        server = poplib.POP3_SSL(
            MAIL_HOST,
            port,
        )
    else:
        server = poplib.POP3(
            MAIL_HOST,
            port,
        )

    server.user(MAIL_USERNAME)
    server.pass_(MAIL_PASSWORD)

    return server


def read_email_by_uuid(server, uuid):

    messages = len(server.list()[1])

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
                return mail

    return None

