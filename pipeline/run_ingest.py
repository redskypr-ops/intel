"""Scheduled entrypoint: ingest -> filter -> enrich -> write to Notion -> alert.

Run via `python -m pipeline.run_ingest [client_slug ...]`. With no args, runs
every client config under config/clients/. Intended to be invoked frequently
(e.g. every 30 min) by .github/workflows/pipeline.yml.
"""
from __future__ import annotations

import sys

from pipeline.config import ClientConfig, load_client_config, load_client_configs
from pipeline.enrich.claude_enrich import enrich
from pipeline.filter.matcher import filter_items
from pipeline.ingest.rss_source import fetch_all_rss
from pipeline.ingest.slack_source import fetch_new_messages
from pipeline.notion.signals import already_captured, create_signal
from pipeline.output.slack_output import post_alert
from pipeline.state import get_cursor, load_state, save_state, set_cursor


def run_for_client(config: ClientConfig, state: dict) -> None:
    oldest = get_cursor(state, config.slug)
    slack_items, new_cursor = fetch_new_messages(config, oldest)
    rss_items = fetch_all_rss(config)
    all_items = slack_items + rss_items

    filtered = filter_items(all_items, config)

    processed = 0
    skipped_duplicate = 0
    skipped_irrelevant = 0
    alerts_sent = 0

    for item in filtered:
        if already_captured(item.raw.link):
            skipped_duplicate += 1
            continue

        enriched = enrich(item, config)
        if not enriched.is_relevant:
            skipped_irrelevant += 1
            continue

        notion_url = create_signal(enriched, config)
        processed += 1

        if item.risk_tripped or enriched.risk == "Alert":
            post_alert(enriched, config, notion_url)
            alerts_sent += 1

    if new_cursor:
        set_cursor(state, config.slug, new_cursor)

    print(
        f"[{config.slug}] fetched={len(all_items)} matched={len(filtered)} "
        f"created={processed} duplicates_skipped={skipped_duplicate} "
        f"irrelevant_skipped={skipped_irrelevant} alerts={alerts_sent}"
    )


def main(argv: list[str]) -> None:
    configs = [load_client_config(slug) for slug in argv] if argv else load_client_configs()
    state = load_state()
    for config in configs:
        run_for_client(config, state)
    save_state(state)


if __name__ == "__main__":
    main(sys.argv[1:])
