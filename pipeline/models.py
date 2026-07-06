"""Shared item shapes passed between pipeline layers."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RawItem:
    """One candidate item pulled straight from a source, before filtering."""

    client_slug: str
    source_type: str  # MuckRack | TVEyes | Google Alert | Reddit | Social | RSS | Gmail-Tourism
    source_channel: str  # e.g. "#ifsd91-firehose" or the RSS feed URL
    headline: str
    link: str
    snippet: str  # raw text used for keyword matching + enrichment context
    published_at: str | None = None  # ISO 8601 if known


@dataclass
class FilteredItem:
    """A RawItem that survived the keyword/entity gate."""

    raw: RawItem
    risk_tripped: bool  # matched a risk_keyword -> candidate for immediate alert


@dataclass
class EnrichedItem:
    """A FilteredItem after the single Claude enrichment call."""

    filtered: FilteredItem
    summary: str
    topic_tags: list[str]
    risk: str  # Low | Watch | Alert
    is_relevant: bool
