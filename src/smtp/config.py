"""Загрузка и проверка настроек почтового тестового сервера."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _port_list(name, default):
    """Разобрать список TCP-портов, заданный через запятую."""
    value = os.getenv(name, default)
    try:
        ports = tuple(int(port.strip()) for port in value.split(",") if port.strip())
    except ValueError as error:
        raise RuntimeError(f"{name} must be a comma-separated list of port numbers") from error

    if not ports or any(not 1 <= port <= 65535 for port in ports):
        raise RuntimeError(f"{name} must contain valid TCP port numbers")

    return ports


MAIL_HOST = os.getenv("MAIL_HOST") or os.getenv("HOST_MAIL", "")
MAIL_USERNAME = os.getenv("MAIL_USERNAME") or os.getenv("USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD") or os.getenv("PASSWORD_MAIL", "")
MAIL_FROM = os.getenv("MAIL_FROM", "")
MAIL_TO = os.getenv("MAIL_TO", "")
MAIL_TIMEOUT_SECONDS = int(os.getenv("MAIL_TIMEOUT_SECONDS", "20"))
SMTP_TEST_PORTS = _port_list("SMTP_TEST_PORTS", "25,587")
POP3_TEST_PORTS = _port_list("POP3_TEST_PORTS", "110,995")
IMAP_TEST_PORTS = _port_list("IMAP_TEST_PORTS", "143,993")


def validate_mail_config():
    """Проверить, что заданы сервер, учётные данные и адреса тестовой почты."""
    missing = [
        name
        for name, value in (
            ("MAIL_HOST", MAIL_HOST),
            ("MAIL_USERNAME", MAIL_USERNAME),
            ("MAIL_PASSWORD", MAIL_PASSWORD),
            ("MAIL_FROM", MAIL_FROM),
            ("MAIL_TO", MAIL_TO),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Для почтовых тестов не заданы: " + ", ".join(missing)
        )