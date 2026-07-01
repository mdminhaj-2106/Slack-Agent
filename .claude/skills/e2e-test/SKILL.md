---
name: e2e-test
description: Plan and run end-to-end verification for complete user journeys across web, API, database, and async flows.
---

## Objective
Verify complete journeys work across all layers (Slack event → handler → FastAPI/Canvas → response).

## Environment setup
```bash
pip install -r requirements.txt
cp .env.example .env   # fill in SLACK_BOT_TOKEN, SLACK_APP_TOKEN, SLACK_SIGNING_SECRET
python main.py
curl http://localhost:8000/health
```
Then `@mention` the bot in a real Slack workspace/channel where it's installed and confirm the reply.

## Journey matrix
> Fill from PRD.md critical paths. Currently: (1) `@mention` → "hello" reply, (2) `/health` → `{"status": "ok"}`. Future: decision capture confirm loop, `/why` retrieval, commitment verification nudge.

## Validation layers
Unit → integration (Slack event → handler) → Canvas/pointer-store assertions (once built) → manual Slack workspace check.

## Test commands
No automated test runner exists yet. Manual smoke test is the current gate: `python main.py` + real Slack mention.

## Report format
Environment/branch, test data created, journeys passed/failed, evidence for failures, follow-up issues.

## When to use
Before merging PRs touching Slack event handling or the Canvas schema, before any release, after Slack app config changes (scopes, event subscriptions).
