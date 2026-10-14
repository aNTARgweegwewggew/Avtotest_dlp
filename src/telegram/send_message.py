"""Создание Telegram-клиента и отправка сообщения от пользователя."""

import os
from pathlib import Path

from dotenv import load_dotenv
from telethon.sync import TelegramClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def create_telegram_client():
    """Создать клиент Telegram из API-настроек в файле .env."""
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        raise ValueError("Заполни TELEGRAM_API_ID и TELEGRAM_API_HASH в .env")

    try:
        api_id_number = int(api_id)
    except ValueError as error:
        raise ValueError("TELEGRAM_API_ID должен быть числом") from error

    session_path = PROJECT_ROOT / "secrets" / "telegram_user"
    session_path.parent.mkdir(parents=True, exist_ok=True)

    return TelegramClient(str(session_path), api_id_number, api_hash)


def send_message(username, message):
    """Отправить сообщение от личного Telegram-аккаунта и вернуть его ID."""
    if not username or not username.strip():
        raise ValueError("Укажи получателя Telegram")
    if not message or not message.strip():
        raise ValueError("Текст сообщения не должен быть пустым")

    client = create_telegram_client()
    try:
        client.start()
        sent_message = client.send_message(username.strip(), message)
        return sent_message.id
    finally:
        client.disconnect()
