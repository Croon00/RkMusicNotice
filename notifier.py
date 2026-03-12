import time

import requests

from models import BoothItem

ALERT_NEW = "new"
ALERT_REMINDER_24H = "reminder_24h"
ALERT_SOLD_OUT = "sold_out"
ALERT_ENDED = "ended"


def _artist_color(artist: str | None) -> int:
    if not artist:
        return 0x5865F2
    return (sum(ord(ch) for ch in artist) * 97) % 0xFFFFFF


def _alert_title_prefix(alert_type: str) -> str:
    if alert_type == ALERT_NEW:
        return "[NEW]"
    if alert_type == ALERT_REMINDER_24H:
        return "[D-1]"
    if alert_type == ALERT_SOLD_OUT:
        return "[SOLD OUT]"
    if alert_type == ALERT_ENDED:
        return "[END]"
    return "[INFO]"


def _alert_description(alert_type: str) -> str:
    if alert_type == ALERT_NEW:
        return "새 상품이 등록되었습니다."
    if alert_type == ALERT_REMINDER_24H:
        return "이 상품은 24시간 이내에 종료됩니다."
    if alert_type == ALERT_SOLD_OUT:
        return "이 상품은 현재 품절 상태입니다."
    if alert_type == ALERT_ENDED:
        return "이 상품의 판매가 종료되었습니다."
    return "Item notification."


def _build_message(item: BoothItem, alert_type: str) -> dict:
    status = []
    if item.is_end_of_sale:
        status.append("판매 종료")
    if item.is_sold_out:
        status.append("품절")
    status_text = ", ".join(status) if status else "판매 중"

    sale_end = item.sale_end_at or "-"
    embed = {
        "author": {"name": f"ARTIST | {item.artist or 'UNKNOWN'}"},
        "title": f"{_alert_title_prefix(alert_type)} {item.name or '(no name)'}",
        "url": item.url,
        "color": _artist_color(item.artist),
        "description": (
            f"{_alert_description(alert_type)}\n\n"
            f"가격: {item.price or '-'}\n"
            f"Item ID: {item.item_id or '-'}\n"
            f"상태: {status_text}\n"
            f"판매 종료 기간: {sale_end}"
        ),
        "footer": {"text": "RkMusicNotice"},
    }

    if item.image_url:
        embed["thumbnail"] = {"url": item.image_url}

    return {"embeds": [embed]}


def send_discord_webhook(
    webhook_url: str,
    payload: dict,
    timeout: int                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         = 10,
    max_retries_on_429: int = 5,                                                        
) -> bool:
    for attempt in range(max_retries_on_429 + 1):
        resp = requests.post(webhook_url, json=payload, timeout=timeout)
        if resp.status_code != 429:
            resp.raise_for_status()
            return True

        retry_after_sec = 1.0
        try:
            body = resp.json()
            retry_after_sec = float(body.get("retry_after", retry_after_sec))
        except Exception:
            header_retry = resp.headers.get("Retry-After")
            if header_retry:
                try:
                    retry_after_sec = float(header_retry)
                except ValueError:
                    retry_after_sec = 1.0

        if attempt >= max_retries_on_429:
            break

        retry_after_sec = max(retry_after_sec, 0.5)
        print(f"[WARN] discord 429 rate limit. retry_after={retry_after_sec}s attempt={attempt + 1}")
        time.sleep(retry_after_sec)

    return False


def notify_items_to_discord(
    items: list[BoothItem],
    artist_webhook_urls: dict[str, str],
    default_webhook_url: str = "",
    alert_type: str = ALERT_NEW,
) -> tuple[int, int, list[str]]:
    sent = 0
    skipped = 0
    sent_urls: list[str] = []

    for item in items:
        webhook_url = artist_webhook_urls.get(item.artist or "", "") or default_webhook_url
        if not webhook_url:
            skipped += 1
            print(f"[WARN] artist={item.artist}, webhook not configured -> skip")
            continue

        if not item.url:
            skipped += 1
            print(f"[WARN] artist={item.artist}, item_id={item.item_id}, empty url -> skip")
            continue

        try:
            payload = _build_message(item, alert_type=alert_type)
            ok = send_discord_webhook(webhook_url, payload)
            if ok:
                sent += 1
                sent_urls.append(item.url)
                print(
                    "[INFO] discord sent "
                    f"alert_type={alert_type}, artist={item.artist}, item_id={item.item_id}"
                )
            else:
                print(
                    "[ERROR] discord send failed after retries "
                    f"alert_type={alert_type}, artist={item.artist}, item_id={item.item_id}"
                )
        except Exception as e:
            print(
                "[ERROR] discord send failed "
                f"alert_type={alert_type}, artist={item.artist}, item_id={item.item_id}, error={e}"
            )

    return sent, skipped, sent_urls
