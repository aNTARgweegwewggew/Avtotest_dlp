"""Общие настройки и фикстуры интеграционных тестов pytest."""

import json
import logging
import os
import time
import uuid
from pathlib import Path

import psycopg2
import pytest
import requests
from dotenv import load_dotenv

from src.mail.http_client import create_http_session
from src.mail.yanex_disk_upload import (
    RETRYABLE_STATUS_CODES,
    create_directory,
    delete_path,
)
from src.smtp.config import (
    PROJECT_ROOT,
)
from src.smtp.read_mail_imap import connect_imap, read_email_by_uuid as read_imap_email
from src.smtp.read_mail_pop3 import connect_pop3, read_email_by_uuid as read_pop3_email


logger = logging.getLogger(__name__)
load_dotenv(PROJECT_ROOT / ".env")


class SecretString(str):
    """Скрыть значение токена в выводе pytest."""

    def __repr__(self):
        """Вернуть безопасное представление вместо значения секрета."""
        return "<redacted>"


@pytest.fixture(scope="session")
def get_db_connection():
    """Подключиться к PostgreSQL или пропустить тест, если БД не настроена."""
    settings = {
        "dbname": os.getenv("DB_NAME") or os.getenv("dbname"),
        "user": os.getenv("DB_USER") or os.getenv("user"),
        "password": os.getenv("DB_PASSWORD") or os.getenv("password"),
        "host": os.getenv("DB_HOST") or os.getenv("host"),
        "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
    }
    missing = [
        name
        for name in ("dbname", "user", "password", "host")
        if not settings[name]
    ]
    if missing:
        if len(missing) == 4:
            pytest.skip("Настройки PostgreSQL не заданы; проверка инцидента пропущена")
        raise RuntimeError(
            "Для подключения к PostgreSQL не заданы: " + ", ".join(missing)
        )

    connection = psycopg2.connect(**settings)
    logger.info("Подключение к настроенной базе DLP установлено")
    try:
        yield connection
    finally:
        connection.close()
        logger.info("Подключение к базе DLP закрыто")


def _read_yandex_token_file(token_file):
    """Прочитать токены Яндекса, не раскрывая их в тексте ошибок."""
    if not token_file.is_file():
        raise FileNotFoundError(f"Не найден файл токена Яндекса: {token_file}")

    try:
        token_data = json.loads(token_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Не удалось прочитать файл токена Яндекса ({type(error).__name__})"
        ) from None

    if not isinstance(token_data, dict):
        raise RuntimeError(
            "Файл токена Яндекса должен содержать JSON-объект"
        )

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    if not access_token or not refresh_token:
        raise RuntimeError(
            "В файле токена Яндекса должны быть access_token и refresh_token"
        )

    return token_data


def _save_token_file(token_file, contents):
    """Атомарно сохранить OAuth-токен с доступом только владельцу файла."""
    temporary_file = token_file.with_name(
        f".{token_file.name}.{uuid.uuid4().hex}.tmp"
    )
    file_descriptor = os.open(
        temporary_file,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as token_stream:
            token_stream.write(contents)
        os.chmod(temporary_file, 0o600)
        temporary_file.replace(token_file)
    except Exception:
        temporary_file.unlink(missing_ok=True)
        raise


def _refresh_yandex_token(token_data, token_file):
    """Обновить и безопасно сохранить OAuth-токены Яндекс.Диска."""
    client_id = os.getenv("YANDEX_CLIENT_ID")
    client_secret = os.getenv("YANDEX_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Для обновления токена задайте YANDEX_CLIENT_ID и YANDEX_CLIENT_SECRET"
        )

    try:
        with create_http_session() as session:
            response = session.post(
                "https://oauth.yandex.ru/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": token_data["refresh_token"],
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                timeout=(10, 30),
            )
    except requests.RequestException as error:
        raise RuntimeError(
            f"Не удалось обновить OAuth-токен Яндекса ({type(error).__name__})"
        ) from None

    if not response.ok:
        raise RuntimeError(
            f"Яндекс отклонил обновление токена: HTTP {response.status_code}"
        )

    refreshed_data = response.json()
    if not refreshed_data.get("access_token") or not refreshed_data.get(
        "refresh_token"
    ):
        raise RuntimeError("Ответ OAuth Яндекса не содержит оба токена")

    _save_token_file(token_file, json.dumps(refreshed_data, indent=2))
    logger.info("OAuth-токен Яндекс.Диска обновлён")
    return SecretString(refreshed_data["access_token"])


@pytest.fixture(scope="session")
def yandex_token():
    """Загрузить токен Яндекса и обновить его при ответе HTTP 401."""
    configured_path = os.getenv("YANDEX_TOKEN_FILE")
    if not configured_path:
        pytest.skip(
            "Задайте YANDEX_TOKEN_FILE, чтобы включить тесты Яндекс.Диска"
        )

    token_file = Path(configured_path).expanduser()
    if not token_file.is_absolute():
        token_file = PROJECT_ROOT / token_file
    token_data = _read_yandex_token_file(token_file)

    with create_http_session() as session:
        for attempt in range(3):
            try:
                response = session.get(
                    "https://cloud-api.yandex.net/v1/disk/",
                    headers={"Authorization": f"OAuth {token_data['access_token']}"},
                    timeout=(10, 30),
                )
            except requests.RequestException as error:
                if attempt == 2:
                    raise RuntimeError(
                        "Не удалось проверить OAuth-токен Яндекса "
                        f"({type(error).__name__}) после трёх попыток"
                    ) from None
                logger.warning(
                    "Проверка токена Яндекса не удалась (%s); повтор",
                    type(error).__name__,
                )
                time.sleep(2**attempt)
                continue

            if (
                response.status_code in RETRYABLE_STATUS_CODES
                and attempt < 2
            ):
                logger.warning(
                    "Проверка токена Яндекса вернула HTTP %s; повтор",
                    response.status_code,
                )
                time.sleep(2**attempt)
                continue
            break

    if response.status_code == 401:
        return _refresh_yandex_token(token_data, token_file)
    if not response.ok:
        raise RuntimeError(
            f"Проверка токена Яндекс.Диска завершилась с HTTP {response.status_code}"
        )

    logger.info("OAuth-токен Яндекс.Диска проверен")
    return SecretString(token_data["access_token"])


@pytest.fixture
def yandex_mail_token():
    """Прочитать OAuth-токен для SMTP-отправки через Яндекс.Почту."""
    configured_path = os.getenv("YANDEX_MAIL_TOKEN_FILE")
    if not configured_path:
        pytest.skip(
            "Задайте YANDEX_MAIL_TOKEN_FILE, чтобы включить тесты Яндекс.Почты"
        )

    token_file = Path(configured_path).expanduser()
    if not token_file.is_absolute():
        token_file = PROJECT_ROOT / token_file
    if not token_file.is_file():
        raise FileNotFoundError(
            f"Не найден файл OAuth-токена Яндекс.Почты: {token_file}"
        )

    try:
        token_data = json.loads(token_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            "Не удалось прочитать файл OAuth-токена Яндекс.Почты "
            f"({type(error).__name__})"
        ) from None

    if not isinstance(token_data, dict):
        raise RuntimeError(
            "Файл OAuth-токена Яндекс.Почты должен содержать JSON-объект"
        )

    access_token = token_data.get("access_token")
    if not access_token:
        raise RuntimeError(
            "В файле OAuth-токена Яндекс.Почты отсутствует access_token"
        )

    return SecretString(access_token)


@pytest.fixture
def google_token():
    """Загрузить или обновить OAuth-токен Google Drive для тестов."""
    configured_path = os.getenv("GOOGLE_DRIVE_TOKEN_FILE")
    token_file = (
        Path(configured_path).expanduser()
        if configured_path
        else PROJECT_ROOT / "google_drive_token.json"
    )
    if not token_file.is_file():
        pytest.skip(
            "Задайте GOOGLE_DRIVE_TOKEN_FILE с OAuth-токеном Google Drive"
        )

    from google.auth.transport.requests import Request
    from google.auth.exceptions import RefreshError
    from google.oauth2.credentials import Credentials

    credentials = Credentials.from_authorized_user_file(
        str(token_file),
        ["https://www.googleapis.com/auth/drive"],
    )
    if not credentials.valid:
        try:
            with create_http_session() as session:
                credentials.refresh(Request(session=session))
        except (requests.RequestException, RefreshError, OSError) as error:
            logger.error(
                "Не удалось обновить OAuth-токен Google Drive (%s)",
                type(error).__name__,
            )
            raise RuntimeError(
                "Не удалось обновить OAuth-токен Google Drive; "
                "проверьте доступ к Google API и настройки OAuth"
            ) from None

        _save_token_file(token_file, credentials.to_json())
        logger.info("OAuth-токен Google Drive обновлён")

    logger.info("OAuth-токен Google Drive готов к использованию")
    return SecretString(credentials.token)


@pytest.fixture
def find_received_email():
    """Ожидать письмо с заданным ID через POP3 или IMAP."""

    def find(protocol, port, unique_id):
        """Искать письмо до таймаута и закрывать соединение после каждой попытки."""
        deadline = time.monotonic() + int(
            os.getenv("MAIL_DELIVERY_TIMEOUT_SECONDS", "60")
        )
        reader = {
            "pop3": (connect_pop3, read_pop3_email),
            "imap": (connect_imap, read_imap_email),
        }.get(protocol.lower())
        if reader is None:
            raise ValueError(f"Неподдерживаемый почтовый протокол: {protocol}")

        connect, read = reader
        logger.info(
            "Ожидание тестового письма %s через %s, порт %s",
            unique_id,
            protocol.upper(),
            port,
        )

        while time.monotonic() < deadline:
            server = connect(port)
            try:
                message = read(server, unique_id)
            finally:
                if protocol.lower() == "pop3":
                    server.quit()
                else:
                    server.logout()

            if message is not None:
                return message
            time.sleep(2)

        raise AssertionError(
            f"Письмо {unique_id} не найдено через {protocol.upper()} "
            f"на порту {port} до истечения таймаута"
        )

    return find


@pytest.fixture
def wait_for_dlp_incident(get_db_connection):
    """Ожидать появления источника DLP-инцидента для ID тестового письма."""
    from src.database.database import get_type_incident_from_db

    def wait(search_id, expected_source=None):
        """Проверять источник инцидента до истечения заданного таймаута."""
        timeout_seconds = int(os.getenv("DLP_INCIDENT_TIMEOUT_SECONDS", "90"))
        deadline = time.monotonic() + timeout_seconds
        logger.info(
            "Ожидание DLP-инцидента не более %s секунд",
            timeout_seconds,
        )

        while time.monotonic() < deadline:
            incident_source = get_type_incident_from_db(
                get_db_connection,
                search_id,
                expected_source=expected_source,
            )
            if incident_source:
                logger.info(
                    "Найден DLP-инцидент, источник: %s",
                    incident_source,
                )
                return incident_source
            time.sleep(2)

        return None

    return wait


@pytest.fixture
def yandex_test_folder(yandex_token):
    """Создать отдельную папку Яндекс.Диска и удалить её после теста."""
    base_folder = os.getenv("YANDEX_DISK_TEST_FOLDER", "/DLP_AUTOTEST").rstrip("/")
    run_folder = f"{base_folder}/run-{uuid.uuid4().hex}"
    create_directory(yandex_token, base_folder)
    create_directory(yandex_token, run_folder)
    logger.info("Создана отдельная тестовая папка Яндекс.Диска")

    try:
        yield yandex_token, run_folder
    finally:
        delete_path(yandex_token, run_folder)


@pytest.fixture
def google_drive_test_folder_id():
    """Вернуть ID настроенной папки Google Drive или пропустить тест."""
    folder_id = os.getenv("GOOGLE_DRIVE_TEST_FOLDER_ID")
    if not folder_id:
        pytest.skip(
            "Задайте GOOGLE_DRIVE_TEST_FOLDER_ID, чтобы включить тесты Drive"
        )
    return folder_id
