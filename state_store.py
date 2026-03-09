import json
from pathlib import Path


def load_seen_urls(state_file: str) -> set[str]:
    path = Path(state_file)
    if not path.exists():
        return set()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        urls = data.get("seen_urls", [])
        return set(urls)
    except Exception as e:
        print(f"[WARN] failed to load state file: {e}")
        return set()


def save_seen_urls(state_file: str, seen_urls: set[str]) -> None:
    path = Path(state_file)
    payload = {"seen_urls": sorted(u for u in seen_urls if u)}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def split_new_items(items, seen_urls: set[str]):
    new_items = []
    all_urls = set(seen_urls)

    for item in items:
        if not item.url:
            continue
        if item.url in all_urls:
            continue

        new_items.append(item)
        all_urls.add(item.url)

    return new_items, all_urls
