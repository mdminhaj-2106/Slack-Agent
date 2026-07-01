# API

## Global standards
- Base path: none (single-service, no `/api` prefix).
- Auth: none on the FastAPI surface (only `/health` exists, no auth needed). Slack-side auth is via bot/app tokens + signing secret, validated at process startup.
- Content type: `application/json`.
- Response envelope: flat JSON, no wrapper — e.g. `{"status": "ok", "service": "recorder-bot"}`.

## Status codes
| Code | Meaning |
|------|---------|
| 200 | Success (only path currently implemented) |

## Authentication
No FastAPI-side auth exists yet. Slack Bolt validates the signing secret internally for HTTP-mode Slack requests, though this app currently uses Socket Mode (no inbound Slack HTTP requests to validate).

## Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness check — returns `{"status": "ok", "service": "recorder-bot"}` |

## Contract rules
- Add new HTTP endpoints only when there's a real external caller (e.g. a future admin dashboard) — Slack interactions themselves go through Socket Mode, not HTTP, in this app.
- Keep `/health` reporting only process liveness, not Slack connection health, unless a watchdog is added (see `architecture.md` risks).

## Planned Slack-side surface (not HTTP — via Socket Mode events, per milestone)
| Milestone | Trigger | Surface |
|-----------|---------|---------|
| M1a | `message`/`app_mention` event, high-confidence classification | Ephemeral Block Kit message with ✓/✗ buttons — visible only to the author |
| M1b | `app_mention` or DM to the bot with `/why [topic]`-shaped text | Reply in-thread with ranked permalinks (must go through the assistant surface, not a slash command, to receive the `action_token`) |
| M2 | Scheduled follow-up on an unverified commitment | Private ephemeral/DM nudge to the owner only |

No new FastAPI HTTP endpoints are planned for M0–M3 — all product surface is Slack-native.
