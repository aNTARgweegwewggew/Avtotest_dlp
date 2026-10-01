from src.mail.search import search_google


def test_google_search():
    response = search_google("secret password")

    assert response.status_code == 200
    assert "secret%20password" in response.url