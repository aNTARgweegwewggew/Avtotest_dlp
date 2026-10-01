import json
import os
from pathlib import Path

import psycopg2
import pytest
import requests
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from src.smtp.read_mail_pop3 import connect_pop3


load_dotenv()


# ============================================================
# DATABASE
# ============================================================

@pytest.fixture(scope="session")
def get_db_connection():
    conn = None

    try:
        conn = psycopg2.connect(
            dbname=os.getenv("dbname"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            host=os.getenv("host"),
        )

        print("Успешное подключение к БД")

        yield conn

    except Exception as e:
        print(f"Ошибка при подключении к БД: {e}")

    finally:
        if conn:
            conn.close()


# ============================================================
# YANDEX DISK
# ============================================================

YANDEX_OAUTH_URL = "https://oauth.yandex.ru/token"
YANDEX_DISK_URL = "https://cloud-api.yandex.net/v1/disk/"
YANDEX_VERIFY_SSL = False

YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID")
YANDEX_CLIENT_SECRET = os.getenv("YANDEX_CLIENT_SECRET")
YANDEX_TOKEN_FILE = Path(os.getenv("YANDEX_TOKEN_FILE"))


def get_yandex_tokens():
    token_data = json.loads(
        YANDEX_TOKEN_FILE.read_text(
            encoding="utf-8"
        )
    )

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    if not access_token:
        raise RuntimeError(
            "В yandex_token.json отсутствует access_token"
        )

    if not refresh_token:
        raise RuntimeError(
            "В yandex_token.json отсутствует refresh_token"
        )

    return access_token, refresh_token


def refresh_yandex_token(refresh_token):
    response = requests.post(
        YANDEX_OAUTH_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": YANDEX_CLIENT_ID,
            "client_secret": YANDEX_CLIENT_SECRET,
        },
        verify=YANDEX_VERIFY_SSL,
        timeout=30,
    )

    response.raise_for_status()

    token_data = response.json()

    access_token = token_data.get("access_token")
    new_refresh_token = token_data.get("refresh_token")

    if not access_token:
        raise RuntimeError(
            "Яндекс не вернул access_token"
        )

    if not new_refresh_token:
        raise RuntimeError(
            "Яндекс не вернул refresh_token"
        )

    YANDEX_TOKEN_FILE.write_text(
        json.dumps(
            token_data,
            indent=2,
        ),
        encoding="utf-8",
    )

    return access_token


@pytest.fixture(scope="session")
def yandex_token():
    access_token, refresh_token = get_yandex_tokens()

    headers = {
        "Authorization": f"OAuth {access_token}"
    }

    response = requests.get(
        YANDEX_DISK_URL,
        headers=headers,
        verify=YANDEX_VERIFY_SSL,
        timeout=30,
    )

    if response.status_code == 200:
        return access_token

    if response.status_code == 401:
        return refresh_yandex_token(refresh_token)

    response.raise_for_status()


# ============================================================
# GOOGLE DRIVE
# ============================================================

GOOGLE_DRIVE_TOKEN_FILE = (
    "/home/user/mail-dlp-automation/google_drive_token.json"
)

GOOGLE_DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive"
]


@pytest.fixture
def google_token():
    credentials = Credentials.from_authorized_user_file(
        GOOGLE_DRIVE_TOKEN_FILE,
        GOOGLE_DRIVE_SCOPES,
    )

    if not credentials.valid:
        session = requests.Session()
        session.verify = False

        request = Request(
            session=session
        )

        credentials.refresh(request)

        with open(
            GOOGLE_DRIVE_TOKEN_FILE,
            "w",
        ) as file:
            file.write(credentials.to_json())

    return credentials.token


# ============================================================
# POP3 / MAILBOX
# ============================================================

def clear_mailbox():

    port = 110

    server = connect_pop3(port)

    messages = len(server.list()[1])

    for i in range(messages, 0, -1):
        server.dele(i)

    server.quit()


@pytest.fixture
def mailbox():
    clear_mailbox()

    yield

    clear_mailbox()

