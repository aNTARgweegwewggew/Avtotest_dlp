
"""Smoke-тест отправки сообщения через Telegram."""

import os
from uuid import uuid4

import pytest

from src.telegram.send_message  import send_message


@pytest.mark.integration
def test_send_message_to_test_user():
    """Отправить уникальное сообщение тестовому пользователю."""
    username = os.getenv("TELEGRAM_TEST_USERNAME")

    if not username:
        pytest.skip("Не задан TELEGRAM_TEST_USERNAME в .env")

    message = f"Проверка отправки DLP автотестом #{uuid4().hex[:8]}"

    message_id = send_message(
        username=username,
        message=message,
    )

    assert isinstance(message_id, int)
    assert message_id > 0
