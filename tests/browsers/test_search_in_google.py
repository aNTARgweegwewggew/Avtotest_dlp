"""Дополнительная проверка доступности поиска Google."""

import os
from urllib.parse import parse_qs, urlsplit

import pytest

from src.mail.search import search_google


pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("RUN_GOOGLE_SEARCH_TESTS") != "1",
    reason="Set RUN_GOOGLE_SEARCH_TESTS=1 to run the external Google search check",
)
def test_google_search():
    """Проверить успешный ответ Google и передачу исходного поискового запроса."""
    response = search_google("secret password")

    assert response.status_code == 200
    assert parse_qs(urlsplit(response.url).query)["q"] == ["secret password"]