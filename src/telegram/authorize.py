"""Однократная интерактивная авторизация личного Telegram-аккаунта."""

import sys

from src.telegram.send_message import create_telegram_client


def main():
    """Создать локальную Telegram-сессию в интерактивном терминале."""
    if not sys.stdin.isatty():
        raise SystemExit(
            "Авторизация Telegram требует интерактивный терминал. "
            "Запусти `.venv/bin/python -m src.telegram.authorize` вручную."
        )

    client = create_telegram_client()
    try:
        client.start()
        if not client.is_user_authorized():
            raise RuntimeError("Telegram не подтвердил авторизацию аккаунта.")
        print("Telegram-сессия успешно сохранена.")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
