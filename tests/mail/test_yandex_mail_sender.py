"""Локальные проверки OAuth-входа и MIME-писем Яндекс.Почты."""

from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock

from src.mail import yandex_mail


def _configure_yandex_mail(monkeypatch, port):
    """Задать фиктивные настройки отдельного ящика Яндекс.Почты."""
    monkeypatch.setenv("YANDEX_MAIL_HOST", "smtp.yandex.com")
    monkeypatch.setenv("YANDEX_MAIL_PORT", str(port))
    monkeypatch.setenv("YANDEX_MAIL_USERNAME", "sender@example.test")
    monkeypatch.setenv("YANDEX_MAIL_TO", "recipient@example.test")


def _message_body(message: Message):
    """Извлечь обычный текст из MIME-письма."""
    body = next(
        part
        for part in message.walk()
        if part.get_content_type() == "text/plain"
        and part.get_content_disposition() != "attachment"
    )
    content = body.get_payload(decode=True)
    assert content is not None
    return content.decode(body.get_content_charset() or "ascii")


def _create_fake_smtp():
    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    smtp.__exit__.return_value = False
    smtp.ehlo.return_value = (250, b"OK")
    auth = {}
    messages = []

    def record_auth(mechanism, response_callback):
        auth["mechanism"] = mechanism
        auth["response"] = response_callback(None)
        return 235, b"Authentication successful"

    smtp.auth.side_effect = record_auth
    smtp.send_message.side_effect = messages.append
    return smtp, auth, messages


def test_sends_text_using_yandex_oauth(monkeypatch):
    """Проверить отправку письма с корректной авторизацией XOAUTH2."""
    _configure_yandex_mail(monkeypatch, 465)
    smtp, auth, messages = _create_fake_smtp()
    monkeypatch.setattr(yandex_mail.smtplib, "SMTP_SSL", lambda *_a, **_k: smtp)

    unique_id = yandex_mail.send_yandex_test_email("test-access-token")

    assert auth["mechanism"] == "XOAUTH2"
    assert auth["response"] == (
        "user=sender@example.test\x01"
        "auth=Bearer test-access-token\x01\x01"
    )
    assert messages[0]["To"] == "recipient@example.test"
    assert _message_body(messages[0]) == (
        f"secret password\nОтправка текста test #{unique_id}"
    )
    assert [
        part
        for part in messages[0].walk()
        if part.get_content_disposition() == "attachment"
    ] == []


def test_sends_one_attachment_using_yandex_starttls(
    monkeypatch,
    tmp_path: Path,
):
    """Проверить отправку одного файла через SMTP с STARTTLS."""
    _configure_yandex_mail(monkeypatch, 587)
    smtp, auth, messages = _create_fake_smtp()
    monkeypatch.setattr(yandex_mail.smtplib, "SMTP", lambda *_a, **_k: smtp)
    attachment = tmp_path / "one.txt"
    attachment.write_text("synthetic one-file content", encoding="utf-8")

    yandex_mail.send_yandex_test_email(
        "test-access-token",
        (attachment,),
    )

    smtp.starttls.assert_called_once()
    assert auth["mechanism"] == "XOAUTH2"
    assert [
        part.get_filename()
        for part in messages[0].walk()
        if part.get_content_disposition() == "attachment"
    ] == ["one.txt"]


def test_sends_two_attachments_using_yandex_oauth(
    monkeypatch,
    tmp_path: Path,
):
    """Проверить отправку двух файлов через SMTP Яндекс.Почты."""
    _configure_yandex_mail(monkeypatch, 465)
    smtp, _auth, messages = _create_fake_smtp()
    monkeypatch.setattr(yandex_mail.smtplib, "SMTP_SSL", lambda *_a, **_k: smtp)
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("synthetic first file", encoding="utf-8")
    second.write_text("synthetic second file", encoding="utf-8")

    yandex_mail.send_yandex_test_email(
        "test-access-token",
        (first, second),
    )

    assert [
        part.get_filename()
        for part in messages[0].walk()
        if part.get_content_disposition() == "attachment"
    ] == ["first.txt", "second.txt"]
