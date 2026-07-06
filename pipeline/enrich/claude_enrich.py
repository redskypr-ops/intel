"""One Claude API call per filtered item: summary, topic tag(s), risk rating.

Runs only on items that already passed the deterministic keyword filter —
this is the token-spend control point the brief calls out. Uses Haiku 4.5
by default (cheap/fast classification+summarization task); override with
ANTHROPIC_MODEL if a higher-quality model is ever warranted for a specific
client.
"""
from __future__ import annotations

import json
import os

import anthropic

from pipeline.config import ClientConfig
from pipeline.models import EnrichedItem, FilteredItem

DEFAULT_MODEL = "claude-haiku-4-5"

# Must exactly match the Topic/Issue multi_select options on the Notion
# Signals database — Notion rejects/ignores values outside this set.
ALLOWED_TOPICS = [
    "Energy",
    "Grid Reliability",
    "Water & Drought",
    "Semiconductors & Workforce",
    "Agriculture & Food",
    "Immigration & Labor",
    "Legislative & Policy",
    "Legal & Regulatory",
    "Economic Development",
    "Education & EdTech",
    "Media & Public Affairs",
    "Data Centers & AI",
    "Governance & Leadership",
    "Crisis/Reputation",
]

_SCHEMA = {
    "type": "object",
    "properties": {
        "is_relevant": {
            "type": "boolean",
            "description": "False if this is a false-positive keyword match with no real connection to the client.",
        },
        "summary": {
            "type": "string",
            "description": "2-4 sentence factual summary of what happened and why it matters to the client.",
        },
        "topic_tags": {
            "type": "array",
            "items": {"type": "string", "enum": ALLOWED_TOPICS},
            "description": "1-3 topic tags that best categorize this item.",
        },
        "risk": {
            "type": "string",
            "enum": ["Low", "Watch", "Alert"],
            "description": "Low: routine coverage. Watch: notable, monitor. Alert: needs immediate attention.",
        },
    },
    "required": ["is_relevant", "summary", "topic_tags", "risk"],
    "additionalProperties": False,
}


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def _prompt(item: FilteredItem, config: ClientConfig) -> str:
    raw = item.raw
    return (
        f"Client: {config.client}\n"
        f"Tracked contacts/entities: {', '.join(config.contacts) or 'n/a'}\n"
        f"Risk tripwire already matched: {item.risk_tripped}\n\n"
        f"Headline: {raw.headline}\n"
        f"Source: {raw.source_type} ({raw.source_channel})\n"
        f"Link: {raw.link}\n"
        f"Content:\n{raw.snippet[:4000]}\n\n"
        "Assess this item for the client above. If it's a false-positive keyword "
        "match with no real connection to the client, set is_relevant to false "
        "and still fill the other fields as best you can."
    )


def enrich(item: FilteredItem, config: ClientConfig, model: str | None = None) -> EnrichedItem:
    client = _client()
    response = client.messages.create(
        model=model or os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL),
        max_tokens=500,
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
        messages=[{"role": "user", "content": _prompt(item, config)}],
    )
    text = next(b.text for b in response.content if b.type == "text")
    data = json.loads(text)
    return EnrichedItem(
        filtered=item,
        summary=data["summary"],
        topic_tags=data["topic_tags"],
        risk=data["risk"],
        is_relevant=data["is_relevant"],
    )
