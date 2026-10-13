"""Создание HTTP-сессии с настройками прокси и доверенных сертификатов."""

import os
from pathlib import Path

import requests


def get_tls_verify():
    """Выбрать CA-сертификат из настроек, системного хранилища или Requests."""
    ca_bundle = os.getenv("REQUESTS_CA_BUNDLE") or os.getenv("CURL_CA_BUNDLE")
    if ca_bundle:
        if not Path(ca_bundle).is_file():
            raise FileNotFoundError(f"CA bundle does not exist: {ca_bundle}")
        return ca_bundle

    tls_verify = os.getenv("TLS_VERIFY", "true").strip().lower()
    if tls_verify in {"0", "false", "no"}:
        return False
    if tls_verify not in {"1", "true", "yes"}:
        raise ValueError("TLS_VERIFY must be true or false")

    system_bundle = Path("/etc/ssl/certs/ca-certificates.crt")
    if system_bundle.is_file():
        return str(system_bundle)

    return True


def create_http_session():
    """Создать HTTP-сессию Requests с выбранной проверкой HTTPS-сертификата."""
    session = requests.Session()
    session.verify = get_tls_verify()
    return session
