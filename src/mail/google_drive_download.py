import pytest
import requests

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


GOOGLE_DRIVE_TOKEN_FILE = (
    "/home/user/mail-dlp-automation/google_drive_token.json"
)

GOOGLE_DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive"
]

FILE_NAME = "12345.txt"

GOOGLE_DRIVE_API = "https://www.googleapis.com/drive/v3/files"


@pytest.fixture
def google_token():
    credentials = Credentials.from_authorized_user_file(
        GOOGLE_DRIVE_TOKEN_FILE,
        GOOGLE_DRIVE_SCOPES
    )

    if not credentials.valid:
        session = requests.Session()
        session.verify = False

        request = Request(session=session)

        credentials.refresh(request)

        with open(GOOGLE_DRIVE_TOKEN_FILE, "w") as file:
            file.write(credentials.to_json())

    return credentials.token


def test_download_file(google_token):
    session = requests.Session()
    session.verify = False

    # Ищем файл по имени
    response = session.get(
        GOOGLE_DRIVE_API,
        headers={
            "Authorization": f"Bearer {google_token}"
        },
        params={
            "q": f"name = '{FILE_NAME}' and trashed = false",
            "fields": "files(id,name)"
        }
    )

    response.raise_for_status()

    files = response.json()["files"]

    if not files:
        raise RuntimeError(f"Файл не найден: {FILE_NAME}")

    file_id = files[0]["id"]

    print(f"Найден файл: {FILE_NAME}")
    print(f"File ID: {file_id}")

    # Скачиваем содержимое файла
    response = session.get(
        f"{GOOGLE_DRIVE_API}/{file_id}",
        headers={
            "Authorization": f"Bearer {google_token}"
        },
        params={
            "alt": "media"
        }
    )

    response.raise_for_status()

    # Сохраняем локально
    with open(FILE_NAME, "wb") as file:
        file.write(response.content)

    print(f"Файл скачан: {FILE_NAME}")