"""Локальные проверки запросов Google Drive на поиск и скачивание."""

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.mail import google_drive_download


def test_find_file_uses_oauth_token(monkeypatch: pytest.MonkeyPatch):
    """Передать OAuth-токен в запрос поиска файла."""
    session = Mock()
    response = Mock(status_code=200)
    response.json.return_value = {"files": [{"id": "test-file-id"}]}
    session.get.return_value = response

    @contextmanager
    def fake_http_session():
        yield session

    monkeypatch.setattr(
        google_drive_download,
        "create_http_session",
        fake_http_session,
    )

    file_id = google_drive_download.find_file_id(
        "test-access-token",
        "test.txt",
    )

    assert file_id == "test-file-id"
    assert session.get.call_args.kwargs["headers"] == {
        "Authorization": "Bearer test-access-token"
    }


def test_download_file_saves_response_body_and_uses_oauth_token(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    """Сохранить скачанные байты и авторизовать запрос."""
    session = Mock()
    response = Mock(status_code=200, content=b"synthetic file content")
    session.get.return_value = response

    @contextmanager
    def fake_http_session():
        yield session

    monkeypatch.setattr(
        google_drive_download,
        "create_http_session",
        fake_http_session,
    )
    destination = tmp_path / "downloads" / "test.txt"

    result = google_drive_download.download_file(
        "test-access-token",
        "test-file-id",
        destination,
    )

    assert result == destination
    assert destination.read_bytes() == b"synthetic file content"
    assert session.get.call_args.kwargs["headers"] == {
        "Authorization": "Bearer test-access-token"
    }
