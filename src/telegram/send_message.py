
"""Отправка сообщений от личного Telegram-аккаунта через Telethon."""

import os
from pathlib import Path

from dotenv import load_dotenv
from telethon.sync import TelegramClient


# Корень проекта: два уровня выше этого файла
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SESSION_DIRECTORY = PROJECT_ROOT / "secrets"
SESSION_PATH = SESSION_DIRECTORY / "telegram_user"

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

    SESSION_DIRECTORY.mkdir(parents=True, exist_ok=True, mode=0o700)
    SESSION_DIRECTORY.chmod(0o700)
    return TelegramClient(str(SESSION_PATH), api_id, api_hash)


def send_message(username: str, message: str) -> int:
    """Отправить сообщение пользователю и вернуть ID отправленного сообщения."""
    if not username or not username.strip():
        raise ValueError("Укажи username получателя Telegram")

    if not message or not message.strip():
        raise ValueError("Текст сообщения не должен быть пустым")

    client = create_telegram_client()

    try:
        client.connect()
        if not client.is_user_authorized():
            raise RuntimeError(
                "Telegram-сессия не авторизована. Сначала выполни "
                "`.venv/bin/python -m src.telegram.authorize` "
                "в интерактивном терминале."
            )

        sent_message = client.send_message(username.strip(), message)
        return sent_message.id
    finally:
        client.disconnect()
def send_file(username,path_to_file):
    if not username or not username.strip():
        raise ValueError("Укажи username получателя Telegram")
    
    if not path_to_file or not path_to_file.strip():
        raise ValueError("Текст сообщения не должен быть пустым")
    
    client = create_telegram_client()

    try:
        client.connect()
        if not client.is_user_authorized():
            raise RuntimeError(
                "Telegram-сессия не авторизована. Сначала выполни "
                "`.venv/bin/python -m src.telegram.authorize` "
                "в интерактивном терминале."
            )
    
        sent_message = client.send_file(username.strip(), path_to_file)
        return sent_message.id
    finally:
            client.disconnect()
    
def send_voice(username,path_to_voice):
    if not username or not username.strip():
        raise ValueError("Укажи username получателя Telegram")
    
    if not path_to_voice or not path_to_voice.strip():
        raise ValueError("Текст сообщения не должен быть пустым")
    
    client = create_telegram_client()

    try:
        client.connect()
        if not client.is_user_authorized():
            raise RuntimeError(
                "Telegram-сессия не авторизована. Сначала выполни "
                "`.venv/bin/python -m src.telegram.authorize` "
                "в интерактивном терминале."
            )
    
        sent_message = client.send_file(username.strip(),path_to_voice, voice_note=True)
        return sent_message.id
    finally:
            client.disconnect()    

def send_video(username,path_to_video):
    if not username or not username.strip():
        raise ValueError("Укажи username получателя Telegram")
    
    if not path_to_video or not path_to_video.strip():
        raise ValueError("Текст сообщения не должен быть пустым")
    
    client = create_telegram_client()

    try:
        client.connect()
        if not client.is_user_authorized():
            raise RuntimeError(
                "Telegram-сессия не авторизована. Сначала выполни "
                "`.venv/bin/python -m src.telegram.authorize` "
                "в интерактивном терминале."
            )
    
        sent_message = client.send_file(username.strip(),path_to_video, video_note=True)
        return sent_message.id
    finally:
            client.disconnect()    