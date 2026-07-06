"""Scheduled entrypoint: post the digest for each client and mark rows Reviewed.

Run via `python -m pipeline.run_digest [client_slug ...]`. Alert-tier items
already posted immediately in run_ingest.py; they're still included in the
digest for a complete record, formatted the same as everything else.
"""
from __future__ import annotations

import sys

from pipeline.config import load_client_config, load_client_configs
from pipeline.notion.signals import mark_reviewed, query_new_signals
from pipeline.output.slack_output import post_digest


def run_for_client(config, period_label: str) -> None:
    rows = query_new_signals(config)
    if not rows:
        print(f"[{config.slug}] nothing to digest")
        return

    items = [item for _, item in rows]
    post_digest(items, config, period_label)

    for page_id, _ in rows:
        mark_reviewed(page_id)

    print(f"[{config.slug}] digested {len(rows)} item(s)")


def main(argv: list[str], period_label: str = "digest") -> None:
    configs = [load_client_config(slug) for slug in argv] if argv else load_client_configs()
    for config in configs:
        run_for_client(config, period_label)


if __name__ == "__main__":
    main(sys.argv[1:])
