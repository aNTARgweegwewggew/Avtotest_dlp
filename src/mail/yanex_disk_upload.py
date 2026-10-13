"""Управление тестовыми папками и файлами на Яндекс.Диске."""

import logging
import time
from pathlib import Path

import requests

from src.mail.http_client import create_http_session


logger = logging.getLogger(__name__)
YANDEX_DISK_RESOURCES_URL = "https://cloud-api.yandex.net/v1/disk/resources"
YANDEX_UPLOAD_URL = f"{YANDEX_DISK_RESOURCES_URL}/upload"
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}


def _headers(access_token):
    """Собрать заголовок авторизации, не выводя токен в журнал."""
    return {"Authorization": f"OAuth {access_token}"}


def _raise_http_error(response, operation):
    """Сообщить об ошибке HTTP, не раскрывая адрес запроса и учётные данные."""
    if not response.ok:
        raise RuntimeError(
            f"Yandex Disk {operation} failed with HTTP {response.status_code}"
        )


def create_directory(access_token, disk_path):
    """Создать папку на Яндекс.Диске или принять уже существующую."""
    with create_http_session() as session:
        response = session.put(
            YANDEX_DISK_RESOURCES_URL,
            headers=_headers(access_token),
            params={"path": disk_path},
            timeout=(10, 30),
        )

    if response.status_code == 409:
        try:
            error_code = response.json().get("error")
        except ValueError:
            error_code = None
        if error_code in {
            "DiskPathPointsToExistentDirectory",
            "DiskPathPointsToExistentDirectoryError",
        }:
            return

    if response.status_code not in {201, 202}:
        _raise_http_error(response, "directory creation")

    logger.info("Created Yandex Disk test directory: %s", disk_path)


def delete_path(access_token, disk_path):
    """Удалить отдельную папку, созданную для текущего запуска."""
    with create_http_session() as session:
        for attempt in range(3):
            try:
                response = session.delete(
                    YANDEX_DISK_RESOURCES_URL,
                    headers=_headers(access_token),
                    params={"path": disk_path, "permanently": "true"},
                    timeout=(10, 30),
                )
            except requests.RequestException as error:
                if attempt == 2:
                    raise RuntimeError(
                        "Не удалось очистить тестовую папку Яндекс.Диска "
                        f"({type(error).__name__})"
                    ) from None
                logger.warning(
                    "Очистка папки Яндекс.Диска не удалась (%s); повтор",
                    type(error).__name__,
                )
                time.sleep(2**attempt)
                continue

            if (
                response.status_code in RETRYABLE_STATUS_CODES
                and attempt < 2
            ):
                logger.warning(
                    "Очистка папки Яндекс.Диска вернула HTTP %s; повтор",
                    response.status_code,
                )
                time.sleep(2**attempt)
                continue
            break

    if response.status_code not in {200, 202, 204, 404}:
        _raise_http_error(response, "test-directory cleanup")

    logger.info("Removed Yandex Disk test directory: %s", disk_path)


def get_upload_url(access_token, disk_path, overwrite=False):
    """Получить временную ссылку для загрузки файла на Яндекс.Диск."""
    with create_http_session() as session:
        for attempt in range(3):
            try:
                response = session.get(
                    YANDEX_UPLOAD_URL,
                    headers=_headers(access_token),
                    params={"path": disk_path, "overwrite": str(overwrite).lower()},
                    timeout=(10, 30),
                )
            except requests.RequestException as error:
                if attempt == 2:
                    raise RuntimeError(
                        f"Yandex Disk upload URL request failed ({type(error).__name__})"
                    ) from None
                time.sleep(2**attempt)
                continue

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < 2:
                logger.warning(
                    "Yandex Disk upload URL returned HTTP %s; retrying",
                    response.status_code,
                )
                time.sleep(2**attempt)
                continue

            if response.status_code != 200:
                _raise_http_error(response, "upload URL request")
                raise RuntimeError(
                    "Yandex Disk upload URL request returned unexpected "
                    f"HTTP {response.status_code}"
                )
            logger.info(
                "Yandex Disk upload URL request completed: HTTP %s",
                response.status_code,
            )
            return response.json()["href"]

    raise RuntimeError("Yandex Disk upload URL retries were exhausted")


def upload_file(access_token, file_path, disk_path, overwrite=False):
    """Передать файл на временную ссылку Яндекс.Диска обычным телом PUT."""
    file_path = Path(file_path)
    file_size = file_path.stat().st_size
    upload_url = get_upload_url(access_token, disk_path, overwrite=overwrite)

    with create_http_session() as session:
        for attempt in range(3):
            try:
                with file_path.open("rb") as file:
                    response = session.put(
                        upload_url,
                        data=file,
                        headers={
                            "Content-Type": "application/octet-stream",
                            "Content-Length": str(file_size),
                        },
                        timeout=(10, 120),
                    )
            except (OSError, requests.RequestException) as error:
                if attempt == 2:
                    raise RuntimeError(
                        f"Yandex Disk upload failed ({type(error).__name__})"
                    ) from None
                time.sleep(2**attempt)
                continue

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < 2:
                logger.warning(
                    "Yandex Disk file upload returned HTTP %s; retrying",
                    response.status_code,
                )
                time.sleep(2**attempt)
                continue

            if response.status_code not in {201, 202}:
                _raise_http_error(response, "file upload")
                raise RuntimeError(
                    f"Yandex Disk file upload returned unexpected HTTP {response.status_code}"
                )
            logger.info(
                "Uploaded Yandex Disk test file: HTTP %s %s bytes=%s",
                response.status_code,
                file_path.name,
                file_size,
            )
            return response.status_code

    raise RuntimeError("Yandex Disk upload retries were exhausted")
