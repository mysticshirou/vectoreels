import requests


def fetch_bytes(url: str, headers: dict[str, str]) -> bytes:
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.content
