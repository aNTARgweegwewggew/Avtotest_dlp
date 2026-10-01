import time

import pytest

from src.smtp.send_mail import send_email
from src.database.database import (
    get_email_body_from_db,
    get_type_incident_from_db,
)


@pytest.mark.parametrize(
    "smtp_port",
    [
        25,
        587,
        pytest.param(
            465,
            marks=pytest.mark.xfail(
                reason="На Romeo отсутствует SMTP + SSL"
            ),
        ),
    ],
)
def test_outgoing_mail(
    get_db_connection,
    smtp_port,
):

    unique_id = send_email(smtp_port)

    time.sleep(3)

    db_text = get_email_body_from_db(
        get_db_connection,
        unique_id,
    )

    incident_type = get_type_incident_from_db(
        get_db_connection,
        unique_id,
    )

    assert incident_type == "Исходящая почта"

    assert db_text == (
        f"Отправка текста test #{unique_id}"
    )