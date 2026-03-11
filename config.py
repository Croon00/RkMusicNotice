import os
import json

BASE_URL = "https://rkmusic.booth.pm"
ITEMS_URL = f"{BASE_URL}/items"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

ARTIST_LISTS = {
    "HACHI": "https://rkmusic.booth.pm/item_lists/rjJT4XGr",
    "KMNZ": "https://rkmusic.booth.pm/item_lists/rooT4603",
    "VESPERBELL": "https://rkmusic.booth.pm/item_lists/nlkToYEv",
    "LIVE UNION": "https://rkmusic.booth.pm/item_lists/mgKTVXvY",
    "?ф댏阿껁겏??": "https://rkmusic.booth.pm/item_lists/nNPTZ1JP",
    "?붼춸?뗣굤": "https://rkmusic.booth.pm/item_lists/mzGTPyjn",
    "麗당???": "https://rkmusic.booth.pm/item_lists/rw9TWW5p",
    "MEDA": "https://rkmusic.booth.pm/item_lists/8xPTooaQ",
    "CULUA": "https://rkmusic.booth.pm/item_lists/mEoT22y2",
    "NEUN": "https://rkmusic.booth.pm/item_lists/8bNT33QW",
    "XIDEN": "https://rkmusic.booth.pm/item_lists/mEoT2AMx",
    "IMI": "https://rkmusic.booth.pm/item_lists/8bNT3pJQ",
    "?ⓦ깕": "https://rkmusic.booth.pm/item_lists/r27TEyMW",
    "CONA": "https://rkmusic.booth.pm/item_lists/8plTeq92",
    "曆긷쉽": "https://rkmusic.booth.pm/item_lists/nlkToK3q",
    "Cil": "https://rkmusic.booth.pm/item_lists/rooT4wJo",
    "獰썹퇁": "https://rkmusic.booth.pm/item_lists/myVTMJKR",
    "LEWNE": "https://rkmusic.booth.pm/item_lists/rM9TpDaM",
    "wouca": "https://rkmusic.booth.pm/item_lists/nqXTgA1O",
}

# Recommended: set this via environment variable / GitHub secret.
DEFAULT_DISCORD_WEBHOOK_URL = os.getenv("DEFAULT_DISCORD_WEBHOOK_URL", "")

# Optional JSON map. Example:
# {"HACHI":"https://discord.com/api/webhooks/...","KMNZ":"https://discord.com/api/webhooks/..."}
DISCORD_WEBHOOK_URLS = json.loads(os.getenv("DISCORD_WEBHOOK_URLS", "{}"))

STATE_FILE = os.getenv("STATE_FILE", "state_seen_urls.json")
# If True and state file is empty/non-existent, first run only saves state without alert.
SKIP_ALERT_ON_FIRST_RUN = os.getenv("SKIP_ALERT_ON_FIRST_RUN", "false").lower() == "true"
