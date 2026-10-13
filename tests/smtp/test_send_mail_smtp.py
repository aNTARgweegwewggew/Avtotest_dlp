"""Проверки регистрации исходящих писем как DLP-инцидентов."""

import logging

import pytest

from src.database.database import get_email_body_from_db
from src.smtp.config import SMTP_TEST_PORTS
from src.smtp.send_mail import build_test_email_body, send_email


logger = logging.getLogger(__name__)


@pytest.mark.parametrize("smtp_port", SMTP_TEST_PORTS)
def test_outgoing_mail_creates_dlp_incident(
    get_db_connection,
    smtp_port,
    wait_for_dlp_incident,
):
    """Проверить наличие письма и связанного DLP-инцидента в БД."""
    unique_id = send_email(smtp_port, include_dlp_marker=True)
    expected_body = build_test_email_body(unique_id, include_dlp_marker=True)

    incident_source = wait_for_dlp_incident(unique_id)
    actual_body = get_email_body_from_db(get_db_connection, unique_id)
    assert actual_body is not None, (
        "Письмо отправлено, но не найдено в zinc_v_blob "
        f"для тестового ID {unique_id}; проверьте регистрацию события в DLP"
    )
    assert incident_source is not None, (
        "Текст письма есть в zinc_v_blob, но источник инцидента не найден "
        f"для тестового ID {unique_id}"
    )
    assert actual_body == expected_body
    logger.info("Проверка исходящего DLP-письма пройдена: ID %s", unique_id)
