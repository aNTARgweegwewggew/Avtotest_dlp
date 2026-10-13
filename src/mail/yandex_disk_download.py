"""Получение списка файлов и скачивание данных с Яндекс.Диска."""

import logging
import time
from pathlib import Path

import requests

from src.mail.http_client import create_http_session


logger = logging.getLogger(__name__)
YANDEX_DOWNLOAD_URL = "https://cloud-api.yandex.net/v1/disk/resources/download"
YANDEX_RESOURCES_URL = "https://cloud-api.yandex.net/v1/disk/resources"
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}


def get_disk_files(access_token, disk_path):
    """Получить имена файлов, расположенных непосредственно в папке."""
    headers = {"Authorization": f"OAuth {access_token}"}

    with create_http_session() as session:
        for attempt in range(3):
            try:
                response = session.get(
                    YANDEX_RESOURCES_URL,
                    headers=headers,
                    params={"path": disk_path},
                    timeout=(10, 30),
                )
            except requests.RequestException as error:
                if attempt == 2:
                    raise RuntimeError(
                        f"Yandex Disk listing failed ({type(error).__name__})"
                    ) from None
                time.sleep(2**attempt)
                continue

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < 2:
                logger.warning(
                    "Yandex Disk listing returned HTTP %s; retrying",
                    response.status_code,
                )
                time.sleep(2**attempt)
                continue

            if response.status_code != 200:
                raise RuntimeError(
                    "Yandex Disk listing returned unexpected "
                    f"HTTP {response.status_code}"
                )

            logger.info("Yandex Disk listing completed: HTTP %s", response.status_code)
            items = response.json().get("_embedded", {}).get("items", [])
            return [
                item["name"]
                for item in items
                if item.get("type") == "file" and "name" in item
            ]

    raise RuntimeError("Yandex Disk listing retries were exhausted")


def get_download_url(access_token, disk_path):
    """Получить временную ссылку для скачивания файла."""
    headers = {"Authorization": f"OAuth {access_token}"}

    with create_http_session() as session:
        for attempt in range(3):
            try:
                response = session.get(
                    YANDEX_DOWNLOAD_URL,
                    headers=headers,
                    params={"path": disk_path},
                    timeout=(10, 30),
                )
            except requests.RequestException as error:
                if attempt == 2:
                    raise RuntimeError(
                        f"Yandex Disk download URL request failed "
                        f"({type(error).__name__})"
                    ) from None
                time.sleep(2**attempt)
                continue

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < 2:
                logger.warning(
                    "Yandex Disk download URL returned HTTP %s; retrying",
                    response.status_code,
                )
                time.sleep(2**attempt)
                continue

            if response.status_code != 200:
                raise RuntimeError(
                    "Yandex Disk download URL request returned unexpected "
                    f"HTTP {response.status_code}"
                )

            logger.info(
                "Yandex Disk download URL request completed: HTTP %s",
                response.status_code,
            )
            return response.json()["href"]

    raise RuntimeError("Yandex Disk download URL retries were exhausted")


def download_file(access_token, disk_path, download_dir):
    """Скачать все файлы из папки и вернуть пути к локальным копиям."""
    download_dir = Path(download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)
    downloaded_files = []

    for file_name in get_disk_files(access_token, disk_path):
        if Path(file_name).name != file_name:
            raise RuntimeError("Yandex Disk returned an invalid file name")

        remote_path = f"{disk_path.rstrip('/')}/{file_name}"
        download_url = get_download_url(access_token, remote_path)

        with create_http_session() as session:
            for attempt in range(3):
                try:
                    response = session.get(
                        download_url,
                        timeout=(10, 60),
                    )
                except requests.RequestException as error:
                    if attempt == 2:
                        raise RuntimeError(
                            f"Yandex Disk download failed ({type(error).__name__})"
                        ) from None
                    time.sleep(2**attempt)
                    continue

                if (
                    response.status_code in RETRYABLE_STATUS_CODES
                    and attempt < 2
                ):
                    logger.warning(
                        "Yandex Disk download returned HTTP %s; retrying",
                        response.status_code,
                    )
                    time.sleep(2**attempt)
                    continue

                if response.status_code != 200:
                    raise RuntimeError(
                        "Yandex Disk file download returned unexpected "
                        f"HTTP {response.status_code}"
                    )

                local_path = download_dir / file_name
                local_path.write_bytes(response.content)
                downloaded_files.append(local_path)
                logger.info(
                    "Downloaded Yandex Disk test file: HTTP %s %s bytes=%s",
                    response.status_code,
                    file_name,
                    len(response.content),
                )
                break
            else:
                raise RuntimeError("Yandex Disk download retries were exhausted")

    return downloaded_files
