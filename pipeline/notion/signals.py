"""Read/write against the Notion Signals database.

Signals DB (created 2026-07-06, lives in the Red Sky Command Center):
  https://app.notion.com/p/9f368810dcb34aeab3df90aa16c1cd66
  data source: collection://17e29327-3cc2-4d02-a119-53179fc3ad9d

Requires a Notion internal integration token (NOTION_API_KEY) that has been
explicitly shared with both the Signals database and the Clients database
(for the relation lookup) — see docs/SETUP.md.

Dedup strategy: query the Signals DB for an existing row with the same Link
before creating a new one. This is the authoritative dedupe (not the local
Slack cursor file), so it's safe even if state.json is stale or lost.
"""
from __future__ import annotations

import datetime
import os

from notion_client import Client

from pipeline.config import ClientConfig
from pipeline.models import EnrichedItem, FilteredItem, RawItem

SIGNALS_DATABASE_ID = "9f368810-dcb3-4aea-b3df-90aa16c1cd66"


def _client() -> Client:
    return Client(auth=os.environ["NOTION_API_KEY"])


def already_captured(link: str) -> bool:
    if not link:
        return False
    notion = _client()
    resp = notion.databases.query(
        database_id=SIGNALS_DATABASE_ID,
        filter={"property": "Link", "url": {"equals": link}},
        page_size=1,
    )
    return len(resp.get("results", [])) > 0


def create_signal(item: EnrichedItem, config: ClientConfig) -> str:
    """Creates the Notion page and returns its URL."""
    notion = _client()
    raw = item.filtered.raw
    properties = {
        "Headline": {"title": [{"text": {"content": raw.headline[:2000]}}]},
        "Source Type": {"select": {"name": raw.source_type}},
        "Source Channel": {"rich_text": [{"text": {"content": raw.source_channel[:2000]}}]},
        "Topic/Issue": {"multi_select": [{"name": t} for t in item.topic_tags]},
        "Risk/Priority": {"select": {"name": item.risk}},
        "Summary": {"rich_text": [{"text": {"content": item.summary[:2000]}}]},
        "Date captured": {"date": {"start": datetime.date.today().isoformat()}},
        "Status": {"select": {"name": "New"}},
    }
    if raw.link:
        properties["Link"] = {"url": raw.link}
    if config.notion_client_page_id:
        properties["Client(s)"] = {"relation": [{"id": config.notion_client_page_id}]}

    page = notion.pages.create(
        parent={"database_id": SIGNALS_DATABASE_ID},
        properties=properties,
    )
    return page["url"]


def _page_to_enriched_item(page: dict) -> EnrichedItem:
    props = page["properties"]
    title = "".join(t["plain_text"] for t in props["Headline"]["title"])
    summary = "".join(t["plain_text"] for t in props["Summary"]["rich_text"])
    link = (props.get("Link") or {}).get("url") or ""
    risk = (props.get("Risk/Priority") or {}).get("select", {}) or {}
    source_channel = "".join(t["plain_text"] for t in props["Source Channel"]["rich_text"])
    raw = RawItem(
        client_slug="",
        source_type=(props.get("Source Type") or {}).get("select", {}).get("name", ""),
        source_channel=source_channel,
        headline=title,
        link=link,
        snippet="",
    )
    return EnrichedItem(
        filtered=FilteredItem(raw=raw, risk_tripped=False),
        summary=summary,
        topic_tags=[o["name"] for o in (props.get("Topic/Issue") or {}).get("multi_select", [])],
        risk=risk.get("name", "Low"),
        is_relevant=True,
    )


def query_new_signals(config: ClientConfig) -> list[tuple[str, EnrichedItem]]:
    """Returns [(page_id, EnrichedItem), ...] for this client's un-digested (Status=New) rows."""
    if not config.notion_client_page_id:
        return []
    notion = _client()
    resp = notion.databases.query(
        database_id=SIGNALS_DATABASE_ID,
        filter={
            "and": [
                {"property": "Status", "select": {"equals": "New"}},
                {"property": "Client(s)", "relation": {"contains": config.notion_client_page_id}},
            ]
        },
    )
    return [(page["id"], _page_to_enriched_item(page)) for page in resp.get("results", [])]


def mark_reviewed(page_id: str) -> None:
    notion = _client()
    notion.pages.update(page_id=page_id, properties={"Status": {"select": {"name": "Reviewed"}}})
