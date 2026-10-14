"""Проверки DLP-инцидентов от отправки писем через Яндекс.Почту."""

from pathlib import Path

import pytest

from src.database.database import get_email_body_from_db
from src.mail.yandex_mail import send_yandex_test_email
from src.smtp.send_mail import build_test_email_body


pytestmark = pytest.mark.integration


MAIL_FILES = Path(__file__).resolve().parents[1] / "data" / "mail"
ONE_ATTACHMENT = (MAIL_FILES / "single" / "avtotest-dlp-marker.txt",)
TWO_ATTACHMENTS = (
    MAIL_FILES / "multiple" / "avtotest-dlp-marker-a.txt",
    MAIL_FILES / "multiple" / "avtotest-dlp-marker-b.txt",
)


def _send_and_check_dlp_mail(
    access_token,
    get_db_connection,
    wait_for_dlp_incident,
    attachment_paths=(),
):
    """Отправить письмо и сравнить его текст и имена вложений с записью DLP."""
    unique_id = send_yandex_test_email(access_token, attachment_paths)
    assert wait_for_dlp_incident(unique_id) is not None, (
        f"Для письма {unique_id} не появился DLP-инцидент в базе"
    )

    actual_body = get_email_body_from_db(get_db_connection, unique_id)
    expected_body = build_test_email_body(unique_id, include_dlp_marker=True)
    assert actual_body == expected_body, (
        f"Текст письма {unique_id} в базе не совпадает с отправленным"
    )

    if attachment_paths:
        actual_names = get_email_body_from_db(
            get_db_connection,
            unique_id,
            attachment=True,
        )
        expected_names = sorted(path.name for path in attachment_paths)
        assert sorted(actual_names) == expected_names, (
            f"Набор вложений письма {unique_id} в базе не совпадает"
        )


def test_yandex_mail_sends_text_and_creates_dlp_incident(
    yandex_mail_token,
    get_db_connection,
    wait_for_dlp_incident,
):
    """Отправить письмо без вложений и проверить его текст в DLP-базе."""
    _send_and_check_dlp_mail(
        yandex_mail_token,
        get_db_connection,
        wait_for_dlp_incident,
    )


def test_yandex_mail_sends_one_attachment_and_creates_dlp_incident(
    yandex_mail_token,
    get_db_connection,
    wait_for_dlp_incident,
):
    """Отправить письмо с одним файлом и проверить его запись в DLP-базе."""
    _send_and_check_dlp_mail(
        yandex_mail_token,
        get_db_connection,
        wait_for_dlp_incident,
        ONE_ATTACHMENT,
    )


def test_yandex_mail_sends_two_attachments_and_creates_dlp_incident(
    yandex_mail_token,
    get_db_connection,
    wait_for_dlp_incident,
):
    """Отправить письмо с двумя файлами и проверить их записи в DLP-базе."""
    _send_and_check_dlp_mail(
        yandex_mail_token,
        get_db_connection,
        wait_for_dlp_incident,
        TWO_ATTACHMENTS,
    )
