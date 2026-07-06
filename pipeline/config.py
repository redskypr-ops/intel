"""Load and validate per-client config YAML files (config/clients/*.yaml)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

CLIENTS_DIR = Path(__file__).resolve().parent.parent / "config" / "clients"


@dataclass
class ClientConfig:
    client: str
    contacts: list[str] = field(default_factory=list)
    slack_channel_name: str | None = None
    slack_channel_id: str | None = None
    google_alerts: list[str] = field(default_factory=list)  # boolean query strings, for setup reference only
    google_alert_feeds: list[str] = field(default_factory=list)  # actual RSS URLs once Chad creates the alerts
    reddit_keywords: list[str] = field(default_factory=list)
    social_handles: list[str] = field(default_factory=list)
    direct_rss: list[str] = field(default_factory=list)
    output_channel_id: str | None = None
    risk_keywords: list[str] = field(default_factory=list)
    topic_tags: list[str] = field(default_factory=list)
    notion_client_page_id: str | None = None
    slug: str = ""

    @property
    def match_terms(self) -> list[str]:
        """Terms used by the filter layer to decide whether an item is relevant."""
        return [*self.contacts, *self.reddit_keywords]


def _load_one(path: Path) -> ClientConfig:
    raw = yaml.safe_load(path.read_text()) or {}
    sources = raw.get("sources", {}) or {}
    return ClientConfig(
        client=raw["client"],
        contacts=raw.get("contacts", []) or [],
        slack_channel_name=sources.get("muckrack_slack_channel"),
        slack_channel_id=sources.get("slack_channel_id"),
        google_alerts=sources.get("google_alerts", []) or [],
        google_alert_feeds=sources.get("google_alert_feeds", []) or [],
        reddit_keywords=sources.get("reddit_keywords", []) or [],
        social_handles=sources.get("social_handles", []) or [],
        direct_rss=sources.get("direct_rss", []) or [],
        output_channel_id=raw.get("output_channel_id"),
        risk_keywords=raw.get("risk_keywords", []) or [],
        topic_tags=raw.get("topic_tags", []) or [],
        notion_client_page_id=raw.get("notion_client_page_id"),
        slug=path.stem,
    )


def load_client_configs(directory: Path = CLIENTS_DIR) -> list[ClientConfig]:
    return [_load_one(p) for p in sorted(directory.glob("*.yaml"))]


def load_client_config(slug: str, directory: Path = CLIENTS_DIR) -> ClientConfig:
    return _load_one(directory / f"{slug}.yaml")
