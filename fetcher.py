import requests
from bs4 import BeautifulSoup

from config import HEADERS


def fetch_html(url: str, timeout: int = 20) -> str:
    print(f"[REQUEST] GET {url}")
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    print(f"[RESPONSE] status={resp.status_code}")
    resp.raise_for_status()
    return resp.text


def fetch_soup(url: str, timeout: int = 20) -> BeautifulSoup:
    html = fetch_html(url, timeout=timeout)
    return BeautifulSoup(html, "html.parser")