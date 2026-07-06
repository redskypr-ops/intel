# Setup — manual steps required before this pipeline runs live

The code in this repo is complete and tested (`pytest tests/`), but it can't
do anything until the following credentials and accounts exist. None of this
can be done by Claude Code — they're browser/account actions on services
Claude Code has no login for.

## 1. Create a dedicated Slack app (bot), separate from the claude.ai connector

The Slack access Chad uses in chat (the claude.ai Slack connector) is
interactive-only — it isn't available to a headless GitHub Action. This
pipeline needs its own Slack app with a bot token.

1. Go to https://api.slack.com/apps → **Create New App** → From scratch.
2. Under **OAuth & Permissions**, add these Bot Token Scopes:
   - `channels:history` (read public channel messages)
   - `channels:read`
   - `groups:history` (read **private** channel messages — `#ifsd91-firehose` is private)
   - `groups:read`
   - `chat:write` (post digests/alerts)
3. **Install to Workspace**, copy the `xoxb-...` Bot User OAuth Token.
4. Invite the bot to every firehose channel it needs to read, and every
   output channel it needs to post to:
   - `#ifsd91-firehose` (private — run `/invite @your-bot-name` in the channel)
   - Any future client channels, as they're onboarded
5. Add the token as a GitHub Actions secret named `SLACK_BOT_TOKEN`
   (repo → Settings → Secrets and variables → Actions → New repository secret).

## 2. Create a Notion internal integration

1. https://www.notion.so/my-integrations → **New integration**, internal,
   in the Red Sky workspace.
2. Copy the "Internal Integration Secret" (`ntn_...` or `secret_...`).
3. Share it with two things (● **Share** button on each page → invite the
   integration by name):
   - The **🚦 Signals** database (created 2026-07-06, lives in the Red Sky
     Command Center: https://app.notion.com/p/9f368810dcb34aeab3df90aa16c1cd66)
   - The **💼 Clients** database (so the pipeline can look up/relate client
     pages) — the "Active Clients" database on the Command Center page.
4. Add it as a GitHub Actions secret named `NOTION_API_KEY`.

**Note:** this is a different credential from the Notion MCP connector used
interactively in claude.ai/Claude Code chat sessions — that one authenticates
*you*, not a headless script.

## 3. Add IFSD91 to the Notion Clients database

IFSD91 doesn't exist as a row in the Clients DB yet (checked 2026-07-06).
Add it, then paste the new page's ID into
`config/clients/ifsd91.yaml` → `notion_client_page_id`. Without this, Signals
still get created but won't show up in the Client(s) relation column.

## 4. Get an Anthropic API key

Standard Anthropic Console API key (not a Claude.ai subscription — this is
billed separately, per the brief's token-cost concern). Add it as a GitHub
Actions secret named `ANTHROPIC_API_KEY`.

## 5. IFSD91-specific source setup (per the build brief)

- **MuckRack saved search** — Boolean string is in `config/clients/ifsd91.yaml`
  as a comment. MuckRack delivery is Slack-only on the current plan, so point
  it at `#ifsd91-firehose`.
- **TVEyes saved search** — see the short queries in the same file.
- **4 Google Alerts**, each with delivery set to "RSS feed" (not email) —
  queries are listed in `ifsd91.yaml` under `google_alerts`. Once created,
  paste the resulting feed URLs (from Google Alerts' RSS icon) into
  `google_alert_feeds` in the same file.
- `#ifsd91-firehose` already exists (Chad created it 2026-07-05) — nothing
  to do here except invite the new Slack bot (step 1 above).

## 6. Verify idahoednews.org has an RSS feed

`ifsd91.yaml` has this commented out under `direct_rss` pending verification
— uncomment once confirmed.

## What's deliberately NOT touched by this pipeline

- The existing Notion-native agent stack (IDLEG Collector/Analyzer, Fringe
  Collector/Analyzer, AI News Collector, etc.) — those are separate, already
  running, and out of scope. This pipeline is additive, for clients not yet
  covered by that stack (starting with IFSD91).
- Reddit ingestion — no connector exists yet (needs Reddit API app
  registration or an RSS.app wrap). Flagged as a known gap in the brief;
  `reddit_keywords` in client configs are wired for filtering but nothing
  ingests from Reddit yet.
- Tourism/Gmail-label ingestion — different shape (Gmail label listener, not
  Slack), not built in this pass.
- The two disabled Cloud Run dashboards (`idaho-monitor`, `media-monitor`) —
  explicitly out of scope per Chad.

## Running it locally to test

```bash
pip install -r requirements.txt
export SLACK_BOT_TOKEN=xoxb-...
export NOTION_API_KEY=ntn_...
export ANTHROPIC_API_KEY=sk-ant-...
python -m pipeline.run_ingest ifsd91
python -m pipeline.run_digest ifsd91
```

## Scaling to more clients

Once IFSD91 is running cleanly end to end, onboarding a new client is:
1. Write `config/clients/<slug>.yaml` (copy `ifsd91.yaml` as a template).
2. Invite the Slack bot to that client's firehose channel.
3. Nothing else — the GitHub Actions workflow already loops over every
   config file in `config/clients/`.
