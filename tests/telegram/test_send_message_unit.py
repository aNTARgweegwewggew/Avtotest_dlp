"""Локальные проверки логики отправки Telegram-сообщений."""

from unittest.mock import Mock

import pytest
import src.telegram.send_message as telegram_sender


def test_send_message_uses_saved_session_without_prompting(monkeypatch):
    """Не запрашивать код входа при обычном запуске pytest."""
    client = Mock()
    client.is_user_authorized.return_value = False
    monkeypatch.setattr(telegram_sender, "create_telegram_client", lambda: client)

    with pytest.raises(RuntimeError, match="telegram.authorize"):
        telegram_sender.send_message("@test_user", "Тестовое сообщение")

    client.connect.assert_called_once()
    client.is_user_authorized.assert_called_once()
    client.start.assert_not_called()
    client.send_message.assert_not_called()
    client.disconnect.assert_called_once()


def test_send_message_returns_sent_message_id(monkeypatch):
    """Вернуть ID сообщения после отправки через сохранённую сессию."""
    client = Mock()
    client.is_user_authorized.return_value = True
    client.send_message.return_value = Mock(id=123)
    monkeypatch.setattr(telegram_sender, "create_telegram_client", lambda: client)

    message_id = telegram_sender.send_message("@test_user", "Тестовое сообщение")

    assert message_id == 123
    client.connect.assert_called_once()
    client.send_message.assert_called_once_with(
        "@test_user",
        "Тестовое сообщение",
    )
    client.disconnect.assert_called_once()
