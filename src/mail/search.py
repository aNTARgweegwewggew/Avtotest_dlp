"""Выполнение запроса к поиску Google для дополнительной проверки связи."""

import logging

import requests

from src.mail.http_client import create_http_session


logger = logging.getLogger(__name__)


def search_google(query):
    """Отправить запрос в Google и вернуть ответ, не записывая запрос в журнал."""
    try:
        with create_http_session() as session:
            response = session.get(
                "https://www.google.com/search",
                params={"q": query},
                timeout=(10, 30),
            )
        logger.info("Google search request completed with HTTP %s", response.status_code)
        return response
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Google search request failed ({type(exc).__name__})"
        ) from None