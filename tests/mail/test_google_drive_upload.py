"""Локальные проверки формирования multipart-запроса Google Drive."""

from contextlib import contextmanager
from pathlib import Path

import pytest

from src.mail import google_drive_upload


class FakeResponse:
    """Поддельный успешный ответ Google Drive."""

    status_code = 201

    @staticmethod
    def json():
        """Вернуть ID файла из ответа на загрузку."""
        return {"id": "synthetic-file-id"}


class FakeSession:
    """Запомнить HTTP-запрос без обращения к Google Drive."""

    def __init__(self):
        self.request = None

    def __enter__(self):
        """Вернуть подменённую HTTP-сессию."""
        return self

    def __exit__(self, *_exc_info):
        """Закрыть подменённую сессию, не скрывая исключения."""
        return False

    def post(self, url, **kwargs):
        """Сохранить параметры и тело запроса, затем вернуть тестовый ответ."""
        self.request = {"url": url, **kwargs}
        self.request["body"] = kwargs["data"]
        return FakeResponse()


def test_upload_file_sends_authorized_single_request_with_complete_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Проверить единый запрос с метаданными, файлом и авторизацией OAuth."""
    local_file = tmp_path / "dlp-sample.txt"
    content = b"secret password"
    local_file.write_bytes(content)
    session = FakeSession()

    @contextmanager
    def fake_http_session():
        """Подменить сетевую сессию локальным объектом-перехватчиком."""
        yield session

    monkeypatch.setattr(
        google_drive_upload,
        "create_http_session",
        fake_http_session,
    )

    result = google_drive_upload.upload_file(
        "test-access-token",
        local_file,
        "test-folder-id",
    )

    request = session.request
    assert result["id"] == "synthetic-file-id"
    assert request["params"] == {"uploadType": "multipart"}
    assert request["headers"]["Authorization"] == "Bearer test-access-token"
    assert request["headers"]["Content-Type"].startswith("multipart/related; boundary=")
    assert len(request["body"]) == int(request["headers"]["Content-Length"])
    assert b'"name":"dlp-sample.txt"' in request["body"]
    assert b'"parents":["test-folder-id"]' in request["body"]
    assert content in request["body"]
