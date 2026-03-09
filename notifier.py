import requests

from models import BoothItem


def _artist_color(artist: str | None) -> int:
    if not artist:
        return 0x5865F2
    # Deterministic color by artist name for visual separation in one channel.
    return (sum(ord(ch) for ch in artist) * 97) % 0xFFFFFF


def _build_message(item: BoothItem) -> dict:
    status = []
    if item.is_end_of_sale:
        status.append("End of sale")
    if item.is_sold_out:
        status.append("Sold out")

    status_text = ", ".join(status) if status else "On sale"

    embed = {
        "author": {"name": f"ARTIST | {item.artist or 'UNKNOWN'}"},
        "title": item.name or "(no name)",
        "url": item.url,
        "color": _artist_color(item.artist),
        "description": (
            f"Price: {item.price or '-'}\n"
            f"Item ID: {item.item_id or '-'}\n"
            f"Status: {status_text}"
        ),
    }

    if item.image_url:
        embed["thumbnail"] = {"url": item.image_url}

    embed["footer"] = {"text": "RkMusicNotice"}

    return {"embeds": [embed]}


def send_discord_webhook(webhook_url: str, payload: dict, timeout: int = 10) -> None:
    resp = requests.post(webhook_url, json=payload, timeout=timeout)
    resp.raise_for_status()


def notify_items_to_discord(
    items: list[BoothItem],
    artist_webhook_urls: dict[str, str],
    default_webhook_url: str = "",
) -> tuple[int, int]:
    sent = 0
    skipped = 0

    for item in items:
        webhook_url = artist_webhook_urls.get(item.artist or "", "") or default_webhook_url
        if not webhook_url:
            skipped += 1
            print(f"[WARN] artist={item.artist}, webhook not configured -> skip")
            continue

        try:
            payload = _build_message(item)
            send_discord_webhook(webhook_url, payload)
            sent += 1
            print(f"[INFO] discord sent artist={item.artist}, item_id={item.item_id}")
        except Exception as e:
            print(f"[ERROR] discord send failed artist={item.artist}, item_id={item.item_id}, error={e}")

    return sent, skipped
