import requests


def search_google(query):
    try:
        response = requests.get(
            f"https://www.google.com/search?q={query}",
            verify=False,
            timeout=30
        )

        return response

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Google search request failed: {exc}"
        ) from exc
search_google("test")