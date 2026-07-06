"""Deterministic keyword/entity filter — the gate that controls LLM spend.

Nothing reaches the Claude enrichment step unless it matches here. No network
calls, no LLM calls: plain case-insensitive substring matching against each
client's contacts/keywords list.
"""
from __future__ import annotations

from pipeline.config import ClientConfig
from pipeline.models import FilteredItem, RawItem


def _contains_any(haystack: str, needles: list[str]) -> bool:
    haystack_lower = haystack.lower()
    return any(needle.lower() in haystack_lower for needle in needles if needle)


def matches_client(item: RawItem, config: ClientConfig) -> bool:
    """True if the item mentions one of the client's tracked contacts/keywords."""
    text = f"{item.headline}\n{item.snippet}"
    return _contains_any(text, config.match_terms)


def risk_tripped(item: RawItem, config: ClientConfig) -> bool:
    """True if the item contains a risk keyword — trips immediate alert, not digest."""
    text = f"{item.headline}\n{item.snippet}"
    return _contains_any(text, config.risk_keywords)


def filter_items(items: list[RawItem], config: ClientConfig) -> list[FilteredItem]:
    return [
        FilteredItem(raw=item, risk_tripped=risk_tripped(item, config))
        for item in items
        if matches_client(item, config)
    ]
