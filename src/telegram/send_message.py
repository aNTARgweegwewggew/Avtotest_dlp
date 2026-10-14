
"""Отправка сообщений от личного Telegram-аккаунта через Telethon."""

import os
from pathlib import Path

from dotenv import load_dotenv
from telethon.sync import TelegramClient


# Корень проекта: два уровня выше этого файла
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Загружаем настройки из .env в корне проекта
load_dotenv(PROJECT_ROOT / ".env")


def create_telegram_client() -> TelegramClient:
    """Создать Telegram-клиент с настройками из .env."""
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id:
        raise ValueError("В .env не задан TELEGRAM_API_ID")

    if not api_hash:
        raise ValueError("В .env не задан TELEGRAM_API_HASH")

    try:
        api_id = int(api_id)
    except ValueError as error:
        raise ValueError("TELEGRAM_API_ID должен быть целым числом") from error

    session_dir = PROJECT_ROOT / "secrets"
    session_dir.mkdir(parents=True, exist_ok=True)

    session_path = session_dir / "telegram_user"

    return TelegramClient(str(session_path), api_id, api_hash)


def send_message(username: str, message: str) -> int:
    """Отправить сообщение пользователю и вернуть ID отправленного сообщения."""
    if not username or not username.strip():
        raise ValueError("Укажи username получателя Telegram")

    if not message or not message.strip():
        raise ValueError("Текст сообщения не должен быть пустым")

    client = create_telegram_client()

    try:
        client.start()
        sent_message = client.send_message(username.strip(), message)
        return sent_message.id
    finally:
        client.disconnect()
