"""Pull new messages from a client's firehose Slack channel.

Uses a dedicated Slack app/bot token (SLACK_BOT_TOKEN), NOT the interactive
claude.ai Slack connector — that connector isn't available to a headless
GitHub Action. See docs/SETUP.md for the one-time Slack app setup Chad needs
to do (create app, install to workspace, invite bot to each firehose
channel).
"""
from __future__ import annotations

import os
import re

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from pipeline.config import ClientConfig
from pipeline.models import RawItem

_URL_RE = re.compile(r"https?://\S+")


def _client() -> WebClient:
    token = os.environ["SLACK_BOT_TOKEN"]
    return WebClient(token=token)


def _headline_from(text: str) -> str:
    first_line = text.strip().splitlines()[0] if text.strip() else "(no text)"
    words = first_line.split()
    return " ".join(words[:16])


def fetch_new_messages(config: ClientConfig, oldest: str | None) -> tuple[list[RawItem], str | None]:
    """Returns (items, new_cursor). new_cursor is None if nothing was fetched."""
    if not config.slack_channel_id:
        return [], oldest

    client = _client()
    items: list[RawItem] = []
    latest_ts = oldest

    try:
        cursor = None
        while True:
            resp = client.conversations_history(
                channel=config.slack_channel_id,
                oldest=oldest,
                cursor=cursor,
                limit=200,
            )
            for msg in resp.get("messages", []):
                text = msg.get("text", "")
                if not text.strip():
                    continue
                urls = _URL_RE.findall(text)
                link = urls[0].rstrip(">").lstrip("<") if urls else ""
                items.append(
                    RawItem(
                        client_slug=config.slug,
                        source_type="MuckRack" if "muckrack" in text.lower() else "TVEyes",
                        source_channel=config.slack_channel_name or config.slack_channel_id,
                        headline=_headline_from(text),
                        link=link,
                        snippet=text,
                    )
                )
                ts = msg.get("ts")
                if ts and (latest_ts is None or ts > latest_ts):
                    latest_ts = ts
            cursor = resp.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
    except SlackApiError as e:
        raise RuntimeError(
            f"Slack fetch failed for {config.slug} ({config.slack_channel_name}): "
            f"{e.response['error']}. Is the bot invited to this channel?"
        ) from e

    return items, latest_ts
