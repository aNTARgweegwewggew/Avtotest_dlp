
"""Smoke-тест отправки сообщения через Telegram."""

import os
from uuid import uuid4

import pytest

from src.telegram.send_message import send_message, send_file


@pytest.mark.integration
def test_send_message_to_test_user():
    """Отправить уникальное сообщение тестовому пользователю."""
    username = os.getenv("TELEGRAM_TEST_USERNAME")

    if not username:
        pytest.skip(
            "Telegram-тест отключён: укажи TELEGRAM_TEST_USERNAME "
            "в .env (шаблон настроек — .env.example)"
        )

    message = f"Проверка отправки DLP автотестом #{uuid4().hex[:8]}"

    message_id = send_message(
        username=username,
        message=message,
    )

    assert isinstance(message_id, int)
    assert message_id > 0

@pytest.mark.integration
def test_send_file_to_test_user():
    """Отправить уникальное файл тестовому пользователю."""
    username = os.getenv("TELEGRAM_TEST_USERNAME")

    if not username:
        pytest.skip(
            "Telegram-тест отключён: укажи TELEGRAM_TEST_USERNAME "
            "в .env (шаблон настроек — .env.example)"
        )

    path_to_folder = "/home/user/telegram_test/123.txt"

    message_id = send_file(
        username=username,
        path_to_file=path_to_folder,
    )

    assert isinstance(message_id, int)
    assert message_id > 0

def test_send_voice_to_test_user():
    """Отправить уникальное файл тестовому пользователю."""
    username = os.getenv("TELEGRAM_TEST_USERNAME")

    if not username:
        pytest.skip(
            "Telegram-тест отключён: укажи TELEGRAM_TEST_USERNAME "
            "в .env (шаблон настроек — .env.example)"
        )

    path_to_folder = "/home/user/telegram_test/test_voice/output.ogg"

    message_id = send_file(
        username=username,
        path_to_file=path_to_folder,
    )

    assert isinstance(message_id, int)
    assert message_id > 0

def test_send_video_to_test_user():
    """Отправить уникальное файл тестовому пользователю."""
    username = os.getenv("TELEGRAM_TEST_USERNAME")

    if not username:
        pytest.skip(
            "Telegram-тест отключён: укажи TELEGRAM_TEST_USERNAME "
            "в .env (шаблон настроек — .env.example)"
        )

    path_to_folder = "/home/user/telegram_test/test_video/output.mp4"

    message_id = send_file(
        username=username,
        path_to_file=path_to_folder,
    )

    assert isinstance(message_id, int)
    assert message_id > 0