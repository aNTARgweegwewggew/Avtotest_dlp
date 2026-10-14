"""Локальная проверка формирования multipart-запроса Google Drive."""

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.mail import google_drive_upload


def test_upload_file_sends_authorized_request_with_complete_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Проверить OAuth-заголовок и тело запроса загрузки файла."""
    local_file = tmp_path / "dlp-sample.txt"
    content = b"secret password"
    local_file.write_bytes(content)
    session = Mock()
    response = Mock(status_code=201)
    response.json.return_value = {"id": "synthetic-file-id"}
    session.post.return_value = response

    @contextmanager
    def fake_http_session():
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

    request = session.post.call_args.kwargs
    assert result["id"] == "synthetic-file-id"
    assert request["params"] == {"uploadType": "multipart"}
    assert request["headers"]["Authorization"] == "Bearer test-access-token"
    assert request["headers"]["Content-Type"].startswith(
        "multipart/related; boundary="
    )
    assert len(request["data"]) == int(request["headers"]["Content-Length"])
    assert b'"name":"dlp-sample.txt"' in request["data"]
    assert b'"parents":["test-folder-id"]' in request["data"]
    assert content in request["data"]
