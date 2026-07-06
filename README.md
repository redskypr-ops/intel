# Red Sky Intelligence Pipeline

Automated media/social/political intelligence monitoring for Red Sky
Strategic Communications clients. Slack (MuckRack/TVEyes) + RSS/Google
Alerts ingestion → deterministic keyword filter → single Claude API call per
surviving item → Notion Signals database → Slack digest/alert.

See `docs/SETUP.md` for the manual account/credential setup required before
this runs live, and the original build brief for full architecture context.

## Architecture

1. **Ingestion** (`pipeline/ingest/`) — Slack bot pulls new messages from
   client firehose channels; RSS/Google Alert feeds pulled on schedule. Code
   only, no LLM calls.
2. **Filter** (`pipeline/filter/`) — deterministic keyword/entity matching
   against each client's config. This is the gate that controls token spend.
3. **Enrichment** (`pipeline/enrich/`) — one Claude API call (Haiku 4.5) per
   filtered item: summary, topic tags, risk rating, relevance check.
4. **Output** (`pipeline/notion/`, `pipeline/output/`) — write to Notion
   Signals DB; immediate Slack alert for Alert-risk items, scheduled digest
   for everything else.

## Layout

```
config/clients/*.yaml      one config per client (see ifsd91.yaml)
pipeline/config.py         client config loader
pipeline/models.py         shared item dataclasses
pipeline/ingest/           Slack + RSS ingestion
pipeline/filter/           keyword/risk matching
pipeline/enrich/           Claude enrichment call
pipeline/notion/           Notion Signals DB read/write
pipeline/output/           Slack digest/alert formatting + posting
pipeline/run_ingest.py     scheduled entrypoint: ingest -> filter -> enrich -> notion -> alert
pipeline/run_digest.py     scheduled entrypoint: digest
.github/workflows/         cron scheduling (GitHub Actions)
tests/                     unit tests for the deterministic filter/config layers
```

## Running tests

```bash
pip install -r requirements.txt
pytest tests/
```
