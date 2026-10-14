"""Локальные проверки OAuth-входа и MIME-писем Яндекс.Почты."""

from email.message import Message
from pathlib import Path

from src.mail import yandex_mail


class FakeSMTP:
    """Записать команды SMTP, не подключаясь к серверу Яндекса."""

    def __init__(self):
        self.auth_mechanism = None
        self.auth_response = None
        self.message = None
        self.started_tls = False

    def __enter__(self):
        """Вернуть подменённое SMTP-соединение."""
        return self

    def __exit__(self, *_exc_info):
        """Закрыть подменённое соединение без подавления ошибок."""
        return False

    def starttls(self):
        """Записать переход на защищённое SMTP-соединение."""
        self.started_tls = True

    def ehlo(self):
        """Имитировать приветствие после перехода на TLS."""
        return 250, b"OK"

    def auth(self, mechanism, response_callback):
        """Сохранить схему авторизации и ответ с токеном."""
        self.auth_mechanism = mechanism
        self.auth_response = response_callback(None)
        return 235, b"Authentication successful"

    def send_message(self, message):
        """Сохранить сформированное письмо."""
        self.message = message


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


def test_sends_text_using_yandex_oauth(
    monkeypatch,
):
    """Проверить отправку текста и передачу токена в XOAUTH2."""
    _configure_yandex_mail(monkeypatch, 465)
    smtp = FakeSMTP()
    monkeypatch.setattr(yandex_mail.smtplib, "SMTP_SSL", lambda *_a, **_k: smtp)

    unique_id = yandex_mail.send_yandex_test_email("test-access-token")

    assert smtp.auth_mechanism == "XOAUTH2"
    assert smtp.auth_response == (
        "user=sender@example.test\x01"
        "auth=Bearer test-access-token\x01\x01"
    )
    assert smtp.message["To"] == "recipient@example.test"
    assert _message_body(smtp.message) == (
        f"secret password\nОтправка текста test #{unique_id}"
    )
    assert [
        part
        for part in smtp.message.walk()
        if part.get_content_disposition() == "attachment"
    ] == []


def test_sends_one_attachment_using_yandex_starttls(
    monkeypatch,
    tmp_path: Path,
):
    """Проверить отправку одного файла через SMTP с STARTTLS."""
    _configure_yandex_mail(monkeypatch, 587)
    smtp = FakeSMTP()
    monkeypatch.setattr(yandex_mail.smtplib, "SMTP", lambda *_a, **_k: smtp)
    attachment = tmp_path / "one.txt"
    attachment.write_text("synthetic one-file content", encoding="utf-8")

    yandex_mail.send_yandex_test_email(
        "test-access-token",
        (attachment,),
    )

    assert smtp.started_tls
    assert smtp.auth_mechanism == "XOAUTH2"
    assert [
        part.get_filename()
        for part in smtp.message.walk()
        if part.get_content_disposition() == "attachment"
    ] == ["one.txt"]


def test_sends_two_attachments_using_yandex_oauth(
    monkeypatch,
    tmp_path: Path,
):
    """Проверить отправку двух файлов через SMTP Яндекс.Почты."""
    _configure_yandex_mail(monkeypatch, 465)
    smtp = FakeSMTP()
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
        for part in smtp.message.walk()
        if part.get_content_disposition() == "attachment"
    ] == ["first.txt", "second.txt"]
