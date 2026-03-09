import html
import json
from typing import List
from bs4 import BeautifulSoup
from models import BoothItem


def parse_item_nodes(soup: BeautifulSoup):
    return soup.select("li.js-mount-point-shop-item-card")


def parse_item_from_node(node, artist: str | None = None) -> BoothItem | None:
    raw_data = node.get("data-item")
    if not raw_data:
        return None

    try:
        decoded = html.unescape(raw_data)
        data = json.loads(decoded)
    except Exception as e:
        print(f"[WARN] data-item parse failed: {e}")
        return None

    image_urls = data.get("thumbnail_image_urls") or []

    return BoothItem(
        item_id=data.get("id"),
        name=data.get("name"),
        price=data.get("price"),
        url=data.get("shop_item_url") or data.get("url"),
        image_url=image_urls[0] if image_urls else None,
        is_end_of_sale=data.get("is_end_of_sale"),
        is_sold_out=data.get("is_sold_out"),
        artist=artist,
    )


def parse_items_from_soup(soup: BeautifulSoup, artist: str | None = None) -> List[BoothItem]:
    nodes = parse_item_nodes(soup)
    print(f"[INFO] found item nodes: {len(nodes)}")

    items: List[BoothItem] = []
    seen_urls = set()

    for node in nodes:
        item = parse_item_from_node(node, artist=artist)
        if item is None:
            continue

        if item.url in seen_urls:
            continue

        seen_urls.add(item.url)
        items.append(item)

    return items