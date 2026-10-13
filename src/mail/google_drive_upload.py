"""Загрузка и удаление тестовых файлов в Google Drive."""

import json
import logging
import mimetypes
import uuid
from pathlib import Path

import requests

from src.mail.http_client import create_http_session


logger = logging.getLogger(__name__)
GOOGLE_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"
UPLOAD_SUCCESS_STATUS_CODES = {200, 201}


def _multipart_parts(file_path, metadata, boundary):
    """Подготовить метаданные и MIME-границы multipart-запроса."""
    encoded_boundary = boundary.encode("ascii")
    metadata_part = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    body_prefix = b"\r\n".join(
        (
            b"--" + encoded_boundary,
            b"Content-Type: application/json; charset=UTF-8",
            b"",
            metadata_part,
        )
    )
    file_prefix = b"\r\n".join(
        (
            b"\r\n--" + encoded_boundary,
            b"Content-Type: " + content_type.encode("ascii"),
            b"",
            b"",
        )
    )
    closing_boundary = b"\r\n--" + encoded_boundary + b"--\r\n"
    return body_prefix, file_prefix, closing_boundary


def _multipart_body(file_path, body_prefix, file_prefix, closing_boundary):
    """Собрать метаданные, содержимое файла и завершающую границу запроса."""
    return b"".join(
        (
            body_prefix,
            file_prefix,
            file_path.read_bytes(),
            closing_boundary,
        )
    )


def upload_file(access_token, file_path, folder_id, file_name=None):
    """Загрузить файл одним запросом и вернуть ответ Google API."""
    file_path = Path(file_path)
    file_size = file_path.stat().st_size
    metadata = {
        "name": file_name or file_path.name,
        "parents": [folder_id],
    }
    boundary = f"avtotest-{uuid.uuid4().hex}"
    body_prefix, file_prefix, closing_boundary = _multipart_parts(
        file_path,
        metadata,
        boundary,
    )
    body = _multipart_body(
        file_path,
        body_prefix,
        file_prefix,
        closing_boundary,
    )
    content_length = len(body)

    try:
        with create_http_session() as session:
            response = session.post(
                GOOGLE_UPLOAD_URL,
                params={"uploadType": "multipart"},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": f"multipart/related; boundary={boundary}",
                    "Content-Length": str(content_length),
                },
                data=body,
                timeout=(10, 120),
            )
    except (OSError, requests.RequestException) as error:
        raise RuntimeError(
            f"Google Drive multipart upload failed ({type(error).__name__})"
        ) from None

    if response.status_code not in UPLOAD_SUCCESS_STATUS_CODES:
        if not response.ok:
            raise RuntimeError(
                f"Google Drive file upload failed with HTTP {response.status_code}"
            )
        raise RuntimeError(
            "Google Drive file upload returned unexpected "
            f"HTTP {response.status_code}"
        )

    result = response.json()
    if not result.get("id"):
        raise RuntimeError("Google Drive upload response did not include a file ID")

    logger.info(
        "Google Drive multipart upload completed: HTTP %s name=%s bytes=%s",
        response.status_code,
        file_path.name,
        file_size,
    )
    return result


def delete_file(access_token, file_id):
    """Удалить из Google Drive тестовый файл по его ID."""
    with create_http_session() as session:
        response = session.delete(
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=(10, 30),
        )

    if response.status_code != 204:
        if not response.ok:
            raise RuntimeError(
                f"Google Drive test-file cleanup failed with HTTP {response.status_code}"
            )
        raise RuntimeError(
            "Google Drive test-file cleanup returned unexpected "
            f"HTTP {response.status_code}"
        )

    logger.info("Google Drive test file removed: HTTP %s", response.status_code)
