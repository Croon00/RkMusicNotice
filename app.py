import time
from datetime import datetime, timedelta, timezone

from config import (
    ARTIST_LISTS,
    DEFAULT_DISCORD_WEBHOOK_URL,
    DISCORD_WEBHOOK_URLS,
    SKIP_ALERT_ON_FIRST_RUN,
    STATE_FILE,
)
from fetcher import extract_sale_end_at, fetch_soup
from models import BoothItem
from notifier import (
    ALERT_ENDED,
    ALERT_NEW,
    ALERT_REMINDER_24H,
    ALERT_SOLD_OUT,
    notify_items_to_discord,
)
from parser import parse_items_from_soup
from state_store import load_state, save_state

UTC = timezone.utc


def is_currently_on_sale(item: BoothItem) -> bool:
    return not bool(item.is_end_of_sale) and not bool(item.is_sold_out)


def build_page_url(base_url: str, page: int) -> str:
    if page == 1:
        return base_url
    return f"{base_url}?page={page}"


def scrape_artist_page(artist: str, base_url: str, page: int):
    url = build_page_url(base_url, page)
    print(f"\n[INFO] Fetching artist={artist}, page={page}")
    print(f"[INFO] url={url}")

    soup = fetch_soup(url)
    items = parse_items_from_soup(soup, artist=artist)
    print(f"[INFO] artist={artist}, page={page}, parsed_items={len(items)}")
    return items


def scrape_artist_items(artist: str, base_url: str, max_pages: int = 2, sleep_sec: float = 1.0):
    artist_items = []
    seen_urls = set()

    for page in range(1, max_pages + 1):
        try:
            page_items = scrape_artist_page(artist, base_url, page)
        except Exception as e:
            print(f"[ERROR] artist={artist}, page={page}, error={e}")
            break

        new_count = 0
        for item in page_items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                artist_items.append(item)
                new_count += 1

        print(f"[INFO] artist={artist}, page={page}, new_items={new_count}")

        if len(page_items) == 0:
            print(f"[INFO] artist={artist}, page={page}, no items found -> stop")
            break

        time.sleep(sleep_sec)

    return artist_items


def scrape_all_artists(max_pages: int = 2, sleep_sec: float = 1.0):
    all_items = []
    global_seen_urls = set()

    for artist, base_url in ARTIST_LISTS.items():
        print(f"\n========== ARTIST: {artist} ==========")
        items = scrape_artist_items(artist, base_url, max_pages=max_pages, sleep_sec=sleep_sec)

        added = 0
        for item in items:
            if item.url not in global_seen_urls:
                global_seen_urls.add(item.url)
                all_items.append(item)
                added += 1

        print(f"[INFO] artist={artist}, total_added={added}")

    return all_items


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        return None


def should_send_24h_reminder(now: datetime, sale_end_at: datetime) -> bool:
    remain = sale_end_at - now
    return timedelta(0) <= remain <= timedelta(hours=24)


def enrich_sale_end_at(item: BoothItem, record: dict) -> None:
    if item.is_end_of_sale:
        return

    if record.get("sale_end_at"):
        item.sale_end_at = record.get("sale_end_at")
        return

    if not item.url:
        return

    try:
        detected = extract_sale_end_at(item.url)
        if detected:
            item.sale_end_at = detected
            record["sale_end_at"] = detected
            print(f"[INFO] sale_end_at detected item_id={item.item_id} value={detected}")
    except Exception as e:
        print(f"[WARN] sale_end_at parse failed item_id={item.item_id}, error={e}")


def main():
    print("[START] booth artist item scrape")
    now = datetime.now(tz=UTC)
    now_iso = now.isoformat()

    items = scrape_all_artists(max_pages=2, sleep_sec=1.0)
    state = load_state(STATE_FILE)
    state_items = state.get("items", {})

    is_first_run = len(state_items) == 0
    new_items_to_notify: list[BoothItem] = []
    remind_items_to_notify: list[BoothItem] = []
    sold_out_items_to_notify: list[BoothItem] = []
    ended_items_to_notify: list[BoothItem] = []

    for item in items:
        if not item.url:
            continue

        url = item.url
        existing = state_items.get(url, {})
        is_new_item = len(existing) == 0

        record = {
            "url": url,
            "item_id": item.item_id,
            "name": item.name,
            "price": item.price,
            "image_url": item.image_url,
            "artist": item.artist,
            "is_end_of_sale": bool(item.is_end_of_sale),
            "is_sold_out": bool(item.is_sold_out),
            "sale_end_at": existing.get("sale_end_at"),
            "new_alert_sent": bool(existing.get("new_alert_sent", False)),
            "reminder_24h_sent": bool(existing.get("reminder_24h_sent", False)),
            "sold_out_alert_sent": bool(existing.get("sold_out_alert_sent", False)),
            "end_alert_sent": bool(existing.get("end_alert_sent", False)),
            "last_seen_at": now_iso,
        }

        enrich_sale_end_at(item, record)

        if is_new_item and not record["new_alert_sent"]:
            # On first baseline run, only alert items that are currently sellable.
            if not is_first_run or is_currently_on_sale(item):
                new_items_to_notify.append(item)

        sale_end_dt = parse_iso_datetime(record.get("sale_end_at"))
        if (
            not is_first_run
            and
            sale_end_dt
            and not item.is_end_of_sale
            and not record["reminder_24h_sent"]
            and should_send_24h_reminder(now, sale_end_dt)
        ):
            item.sale_end_at = record.get("sale_end_at")
            remind_items_to_notify.append(item)

        prev_sold_out = bool(existing.get("is_sold_out", False))
        if (
            item.is_sold_out
            and not item.is_end_of_sale
            and not prev_sold_out
            and not record["sold_out_alert_sent"]
        ):
            if is_first_run:
                record["sold_out_alert_sent"] = True
            else:
                sold_out_items_to_notify.append(item)

        prev_end_of_sale = bool(existing.get("is_end_of_sale", False))
        if item.is_end_of_sale and not prev_end_of_sale and not record["end_alert_sent"]:
            if is_first_run:
                # Suppress historical ended items on first run baseline.
                record["end_alert_sent"] = True
            else:
                item.sale_end_at = record.get("sale_end_at")
                ended_items_to_notify.append(item)

        state_items[url] = record

    state["items"] = state_items

    print(f"\n[RESULT] total_items={len(items)}")
    print(f"[RESULT] new_items={len(new_items_to_notify)}")
    print(f"[RESULT] remind_24h_items={len(remind_items_to_notify)}")
    print(f"[RESULT] sold_out_items={len(sold_out_items_to_notify)}")
    print(f"[RESULT] ended_items={len(ended_items_to_notify)}")

    if is_first_run and SKIP_ALERT_ON_FIRST_RUN:
        print("[INFO] first run detected -> skip discord alerts and save state only")
    else:
        sent_new, skipped_new, sent_new_urls = notify_items_to_discord(
            new_items_to_notify,
            artist_webhook_urls=DISCORD_WEBHOOK_URLS,
            default_webhook_url=DEFAULT_DISCORD_WEBHOOK_URL,
            alert_type=ALERT_NEW,
        )
        sent_rem, skipped_rem, sent_rem_urls = notify_items_to_discord(
            remind_items_to_notify,
            artist_webhook_urls=DISCORD_WEBHOOK_URLS,
            default_webhook_url=DEFAULT_DISCORD_WEBHOOK_URL,
            alert_type=ALERT_REMINDER_24H,
        )
        sent_sold, skipped_sold, sent_sold_urls = notify_items_to_discord(
            sold_out_items_to_notify,
            artist_webhook_urls=DISCORD_WEBHOOK_URLS,
            default_webhook_url=DEFAULT_DISCORD_WEBHOOK_URL,
            alert_type=ALERT_SOLD_OUT,
        )
        sent_end, skipped_end, sent_end_urls = notify_items_to_discord(
            ended_items_to_notify,
            artist_webhook_urls=DISCORD_WEBHOOK_URLS,
            default_webhook_url=DEFAULT_DISCORD_WEBHOOK_URL,
            alert_type=ALERT_ENDED,
        )
        for url in sent_new_urls:
            if url in state_items:
                state_items[url]["new_alert_sent"] = True
        for url in sent_rem_urls:
            if url in state_items:
                state_items[url]["reminder_24h_sent"] = True
        for url in sent_sold_urls:
            if url in state_items:
                state_items[url]["sold_out_alert_sent"] = True
        for url in sent_end_urls:
            if url in state_items:
                state_items[url]["end_alert_sent"] = True

        print(
            "[RESULT] discord_sent="
            f"{sent_new + sent_rem + sent_sold + sent_end}, "
            "discord_skipped="
            f"{skipped_new + skipped_rem + skipped_sold + skipped_end}"
        )

    save_state(STATE_FILE, state)
    print(f"[INFO] saved state file={STATE_FILE}, tracked_items={len(state_items)}")
    print("[END] finished")


if __name__ == "__main__":
    main()
