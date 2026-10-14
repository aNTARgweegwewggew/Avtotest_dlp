"""Простая проверка отправки сообщения Telegram."""

import pytest

from src.telegram import send_message as telegram_sender


TELEGRAM_TEST_USERNAME = "@replace_with_test_username"
TELEGRAM_TEST_MESSAGE = "Проверка отправки сообщения автотестом"


def test_send_message_to_test_user():
    """Отправить реальное тестовое сообщение указанному пользователю."""
    if TELEGRAM_TEST_USERNAME == "@replace_with_test_username":
        pytest.skip("Укажи Telegram-получателя в TELEGRAM_TEST_USERNAME")

    message_id = telegram_sender.send_message(
        TELEGRAM_TEST_USERNAME,
        TELEGRAM_TEST_MESSAGE,
    )

    assert message_id > 0
