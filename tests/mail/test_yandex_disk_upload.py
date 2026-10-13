"""Проверки формата запроса загрузки файла на Яндекс.Диск."""

from contextlib import contextmanager
from pathlib import Path

import pytest
import requests

from src.mail import yanex_disk_upload


class FakeResponse:
    """Имитировать успешный ответ загрузчика Яндекс.Диска."""

    status_code = 201
    ok = True


class FakeSession:
    """Запомнить PUT-запрос, не обращаясь к реальному сервису."""

    def __init__(self):
        self.request = None

    def __enter__(self):
        """Вернуть подменённую HTTP-сессию."""
        return self

    def __exit__(self, *_exc_info):
        """Закрыть подменённую HTTP-сессию без подавления ошибок."""
        return False

    def put(self, url, **kwargs):
        """Сохранить тело запроса и вернуть успешный ответ."""
        self.request = {"url": url, **kwargs}
        self.request["body"] = kwargs["data"].read()
        return FakeResponse()


def test_upload_file_sends_raw_file_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Проверить, что PUT передаёт байты файла, а не multipart-форму."""
    file_path = tmp_path / "test.txt"
    content = b"synthetic DLP test file"
    file_path.write_bytes(content)
    session = FakeSession()

    @contextmanager
    def fake_http_session():
        """Подменить HTTP-сессию для локальной проверки запроса."""
        yield session

    monkeypatch.setattr(
        yanex_disk_upload,
        "create_http_session",
        fake_http_session,
    )
    monkeypatch.setattr(
        yanex_disk_upload,
        "get_upload_url",
        lambda *_args, **_kwargs: "https://upload.example/test",
    )

    status = yanex_disk_upload.upload_file(
        "test-token",
        file_path,
        "/DLP_AUTOTEST/test.txt",
    )

    request = session.request
    assert status == 201
    assert request["body"] == content
    assert "files" not in request
    assert request["headers"]["Content-Type"] == "application/octet-stream"
    assert request["headers"]["Content-Length"] == str(len(content))


def test_delete_path_retries_network_errors(
    monkeypatch: pytest.MonkeyPatch,
):
    """Проверить повтор удаления папки после временной сетевой ошибки."""

    class RetrySession(FakeSession):
        """Имитировать тайм-аут перед успешным удалением."""

        delete_attempts = 0

        def delete(self, *_args, **_kwargs):
            """Вернуть успешный ответ после одного тайм-аута."""
            self.delete_attempts += 1
            if self.delete_attempts == 1:
                raise requests.ReadTimeout
            return type("Response", (), {"status_code": 204})()

    session = RetrySession()

    @contextmanager
    def fake_http_session():
        """Подменить HTTP-сессию для локальной проверки повтора."""
        yield session

    monkeypatch.setattr(
        yanex_disk_upload,
        "create_http_session",
        fake_http_session,
    )
    monkeypatch.setattr(yanex_disk_upload.time, "sleep", lambda *_args: None)

    yanex_disk_upload.delete_path("test-token", "/DLP_AUTOTEST/run-test")

    assert session.delete_attempts == 2
