import imaplib
from email import policy
from email.parser import BytesParser

from src.smtp.config import (
    MAIL_HOST,
    MAIL_USERNAME,
    MAIL_PASSWORD,
)


def connect_imap(port):

    if port == 993:
        server = imaplib.IMAP4_SSL(
            MAIL_HOST,
            port,
        )
    else:
        server = imaplib.IMAP4(
            MAIL_HOST,
            port,
        )

    server.login(
        MAIL_USERNAME,
        MAIL_PASSWORD,
    )

    server.select("INBOX")

    return server


def read_email_by_uuid(server, uuid):
    status, data = server.uid(
        "search",
        None,
        "ALL",
    )

    if status != "OK":
        return None

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
            return mail

    return None