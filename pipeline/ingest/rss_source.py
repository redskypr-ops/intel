"""Fetch items from client-specific RSS/Google Alert feeds.

No auth required. Google Alerts must be created with "Deliver to: RSS feed"
(see docs/SETUP.md) — Chad does this manually in the browser; the resulting
feed URL goes in the client's direct_rss list (Google Alert RSS feeds are
just another RSS URL from this code's perspective).
"""
from __future__ import annotations

import feedparser

from pipeline.config import ClientConfig
from pipeline.models import RawItem


def fetch_feed(url: str, client_slug: str, source_type: str = "RSS") -> list[RawItem]:
    parsed = feedparser.parse(url)
    items: list[RawItem] = []
    for entry in parsed.entries:
        snippet = entry.get("summary", "") or entry.get("title", "")
        items.append(
            RawItem(
                client_slug=client_slug,
                source_type=source_type,
                source_channel=url,
                headline=entry.get("title", "(no title)"),
                link=entry.get("link", ""),
                snippet=snippet,
                published_at=entry.get("published"),
            )
        )
    return items


def fetch_all_rss(config: ClientConfig) -> list[RawItem]:
    items: list[RawItem] = []
    for url in config.direct_rss:
        items.extend(fetch_feed(url, config.slug, source_type="RSS"))
    for url in config.google_alert_feeds:
        items.extend(fetch_feed(url, config.slug, source_type="Google Alert"))
    return items
