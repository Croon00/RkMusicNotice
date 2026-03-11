import json
from pathlib import Path
from typing import Any


def load_state(state_file: str) -> dict[str, Any]:
    path = Path(state_file)
    if not path.exists():
        return {"items": {}}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] failed to load state file: {e}")
        return {"items": {}}

    # Backward compatibility for legacy state format:
    # {"seen_urls": [...]}
    if isinstance(data, dict) and "items" not in data and "seen_urls" in data:
        items = {}
        for url in data.get("seen_urls", []):
            if not url:
                continue
            items[url] = {
                "url": url,
                "new_alert_sent": True,
                "reminder_24h_sent": False,
                "sold_out_alert_sent": False,
                "end_alert_sent": False,
            }
        return {"items": items}

    items = data.get("items")
    if not isinstance(items, dict):
        return {"items": {}}

    return {"items": items}


def save_state(state_file: str, state: dict[str, Any]) -> None:
    path = Path(state_file)
    items = state.get("items", {})
    payload = {"items": items}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
