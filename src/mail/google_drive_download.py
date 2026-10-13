"""Поиск и скачивание файлов из Google Drive."""

import logging
from pathlib import Path

from src.mail.http_client import create_http_session


logger = logging.getLogger(__name__)
GOOGLE_DRIVE_API = "https://www.googleapis.com/drive/v3/files"


def find_file_id(access_token, file_name):
    """Найти ID первого файла с таким именем, который не находится в корзине."""
    escaped_name = file_name.replace("\\", "\\\\").replace("'", "\\'")
    with create_http_session() as session:
        response = session.get(
            GOOGLE_DRIVE_API,
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "q": f"name = '{escaped_name}' and trashed = false",
                "fields": "files(id,name)",
            },
            timeout=(10, 30),
        )

    if response.status_code != 200:
        raise RuntimeError(
            "Google Drive file search returned unexpected "
            f"HTTP {response.status_code}"
        )

    logger.info("Google Drive file search completed: HTTP %s", response.status_code)
    files = response.json().get("files", [])
    if not files:
        raise FileNotFoundError(f"Google Drive file was not found: {file_name}")
    return files[0]["id"]


def download_file(access_token, file_id, destination):
    """Скачать файл Google Drive по ID в указанный локальный путь."""
    with create_http_session() as session:
        response = session.get(
            f"{GOOGLE_DRIVE_API}/{file_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"alt": "media"},
            timeout=(10, 120),
        )

    if response.status_code != 200:
        raise RuntimeError(
            "Google Drive file download returned unexpected "
            f"HTTP {response.status_code}"
        )

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)
    logger.info(
        "Google Drive file download completed: HTTP %s bytes=%s",
        response.status_code,
        len(response.content),
    )
    return destination
