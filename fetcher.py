import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta, timezone

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


JST = timezone(timedelta(hours=9))


def extract_sale_end_at(url: str, timeout: int = 20) -> str | None:
    """
    Extract end datetime from period-like text in item page.
    Expected example:
    2025/10/29 18:00 ~ 2026/01/11 23:59
    """
    soup = fetch_soup(url, timeout=timeout)
    text = soup.get_text("\n", strip=True)
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    datetime_pattern = re.compile(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2}):(\d{2})")

    for line in lines:
        if not any(sep in line for sep in ("~", "\uFF5E", "\u301C")):
            continue

        matches = datetime_pattern.findall(line)
        if len(matches) < 2:
            continue

        try:
            year, month, day, hour, minute = map(int, matches[-1])
            dt = datetime(year, month, day, hour, minute, tzinfo=JST)
            return dt.isoformat()
        except ValueError:
            continue

    return None
