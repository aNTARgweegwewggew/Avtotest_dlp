"""Простая проверка отправки сообщения Telegram."""

from src.telegram import send_message as telegram_sender


def test_send_message_sends_text(monkeypatch):
    """Проверить, что функция передаёт Telegram-клиенту получателя и текст."""
    sent = {}

    class FakeClient:
        def start(self):
            pass

        def send_message(self, username, message):
            sent["username"] = username
            sent["message"] = message
            return type("Message", (), {"id": 1})()

        def disconnect(self):
            pass

    monkeypatch.setattr(
        telegram_sender,
        "create_telegram_client",
        lambda: FakeClient(),
    )

    telegram_sender.send_message("@test_user", "Привет!")

    assert sent == {"username": "@test_user", "message": "Привет!"}
