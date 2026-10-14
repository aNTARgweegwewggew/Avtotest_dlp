"""Проверки формата запроса загрузки файла на Яндекс.Диск."""

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from src.mail import yanex_disk_upload


def test_upload_file_sends_raw_file_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Проверить, что PUT передаёт байты файла, а не multipart-форму."""
    file_path = tmp_path / "test.txt"
    content = b"synthetic DLP test file"
    file_path.write_bytes(content)
    session = Mock()
    response = Mock(status_code=201, ok=True)
    request = {}

    def record_put(url, **kwargs):
        request.update({"url": url, **kwargs})
        request["body"] = kwargs["data"].read()
        return response

    session.put.side_effect = record_put

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

    assert status == 201
    assert request["body"] == content
    assert "files" not in request
    assert request["headers"]["Content-Type"] == "application/octet-stream"
    assert request["headers"]["Content-Length"] == str(len(content))


def test_delete_path_retries_network_errors(
    monkeypatch: pytest.MonkeyPatch,
):
    """Проверить повтор удаления папки после временной сетевой ошибки."""
    session = Mock()
    session.delete.side_effect = [
        requests.ReadTimeout(),
        Mock(status_code=204),
    ]

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

    assert session.delete.call_count == 2
