"""Tiny JSON state store, committed back to the repo by the GitHub Action.

Tracks per-client Slack cursors (oldest unread timestamp) so scheduled runs
don't re-fetch the same messages. Notion itself is the dedupe source of
truth for writes (query by Link before creating a Signal) — this file only
bounds how far back each Slack fetch has to look.
"""
from __future__ import annotations

import json
from pathlib import Path

STATE_PATH = Path(__file__).resolve().parent.parent / "state" / "slack_cursors.json"


def load_state(path: Path = STATE_PATH) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_state(state: dict, path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def get_cursor(state: dict, client_slug: str) -> str | None:
    return state.get(client_slug, {}).get("slack_oldest")


def set_cursor(state: dict, client_slug: str, timestamp: str) -> None:
    state.setdefault(client_slug, {})["slack_oldest"] = timestamp
