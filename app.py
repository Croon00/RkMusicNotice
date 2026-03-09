import time

from config import (
    ARTIST_LISTS,
    DEFAULT_DISCORD_WEBHOOK_URL,
    DISCORD_WEBHOOK_URLS,
    SKIP_ALERT_ON_FIRST_RUN,
    STATE_FILE,
)
from fetcher import fetch_soup
from notifier import notify_items_to_discord
from parser import parse_items_from_soup
from state_store import load_seen_urls, save_seen_urls, split_new_items


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


def main():
    print("[START] booth artist item scrape test")

    items = scrape_all_artists(max_pages=2, sleep_sec=1.0)
    previous_seen_urls = load_seen_urls(STATE_FILE)
    new_items, merged_seen_urls = split_new_items(items, previous_seen_urls)

    print(f"\n[RESULT] total_items={len(items)}\n")
    print(f"[RESULT] new_items={len(new_items)}")

    is_first_run = len(previous_seen_urls) == 0
    if is_first_run and SKIP_ALERT_ON_FIRST_RUN:
        print("[INFO] first run detected -> skip discord alert and save state only")
    else:
        sent, skipped = notify_items_to_discord(
            new_items,
            artist_webhook_urls=DISCORD_WEBHOOK_URLS,
            default_webhook_url=DEFAULT_DISCORD_WEBHOOK_URL,
        )
        print(f"[RESULT] discord_sent={sent}, discord_skipped={skipped}")

    save_seen_urls(STATE_FILE, merged_seen_urls)
    print(f"[INFO] saved state file={STATE_FILE}, seen_urls={len(merged_seen_urls)}")

    for i, item in enumerate(new_items, start=1):
        print(f"[ITEM {i}]")
        print(f" artist        : {item.artist}")
        print(f" id            : {item.item_id}")
        print(f" name          : {item.name}")
        print(f" price         : {item.price}")
        print(f" url           : {item.url}")
        print(f" image_url     : {item.image_url}")
        print(f" is_end_of_sale: {item.is_end_of_sale}")
        print(f" is_sold_out   : {item.is_sold_out}")
        print("-" * 60)

    print("[END] test finished")


if __name__ == "__main__":
    main()
