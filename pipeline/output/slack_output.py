"""Post immediate alerts and scheduled digests to Slack. No LLM calls here —
formatting a list of already-enriched items into a message is plain code."""
from __future__ import annotations

import os

from slack_sdk import WebClient

from pipeline.config import ClientConfig
from pipeline.models import EnrichedItem

RISK_EMOJI = {"Low": "\U0001f7e2", "Watch": "\U0001f7e1", "Alert": "\U0001f534"}


def _client() -> WebClient:
    return WebClient(token=os.environ["SLACK_BOT_TOKEN"])


def _format_item(item: EnrichedItem, notion_url: str | None = None) -> str:
    raw = item.filtered.raw
    emoji = RISK_EMOJI.get(item.risk, "")
    lines = [f"{emoji} *{raw.headline}* ({item.risk})"]
    lines.append(item.summary)
    if raw.link:
        lines.append(raw.link)
    if notion_url:
        lines.append(f"<{notion_url}|View in Notion>")
    return "\n".join(lines)


def post_alert(item: EnrichedItem, config: ClientConfig, notion_url: str | None = None) -> None:
    if not config.output_channel_id:
        return
    _client().chat_postMessage(
        channel=config.output_channel_id,
        text=f":rotating_light: ALERT — {config.client}\n\n{_format_item(item, notion_url)}",
    )


def post_digest(items: list[EnrichedItem], config: ClientConfig, period_label: str) -> None:
    if not config.output_channel_id or not items:
        return
    header = f"*{config.client} — {period_label} digest* ({len(items)} item{'s' if len(items) != 1 else ''})"
    body = "\n\n".join(_format_item(item) for item in items)
    _client().chat_postMessage(
        channel=config.output_channel_id,
        text=f"{header}\n\n{body}",
    )
