# Security

## Auth model
Slack-side: bot token + app token + signing secret, loaded from `.env` at startup; process refuses to start if bot/app tokens are missing (`main.py:33-37`). No user-facing auth exists on the FastAPI surface (only `/health`, no sensitive data).

## Authorization matrix
| Actor | Can do |
|-------|--------|
| Any Slack user in a channel with the bot | `@mention` it, get a reply |
| Anyone with network access to the host | Hit `/health` (no auth — acceptable since it returns no sensitive data) |

## Sensitive data inventory
| Data | Where | Notes |
|------|-------|-------|
| Slack tokens | `.env` (gitignored) | Never log these; `main.py` does not currently log token values |
| Future: message content | Must never be persisted — per `docs/Intitial-research.md`, only evidence pointers (permalink + `ts` + channel id) may be stored at rest |

## Input validation rules
Slack event payloads use `.get()` with defaults (`main.py:57-59`) rather than direct indexing — keep this pattern for all future event handlers since Slack payload shape varies by event type.

## OWASP-relevant risks for this project
| Risk | Status |
|------|--------|
| Secrets in code | Mitigated — tokens loaded from `.env`, which is gitignored |
| Injection | Low surface currently (no DB, no user-controlled queries) — revisit once a Canvas/DB layer is added |
| Broken access control | N/A yet — no auth boundaries beyond Slack's own scopes |

## Required security headers
N/A — `/health` is the only endpoint and returns no sensitive data.

## Secrets management rules
Never commit `.env`. Never log `BOT_TOKEN`/`APP_TOKEN`/`SIGNING_SECRET` values. Rotate tokens if ever exposed (e.g. accidental commit, pasted into a chat).

## Audit log requirements
None yet — becomes relevant once the Canvas pointer store and commitment verifier exist (per PRD, those need an append-only audit trail: superseded decisions link forward rather than being rewritten).

## Dependency scanning
No scanning configured. `requirements.txt` pins exact versions (`fastapi==0.115.0`, `uvicorn==0.30.6`, `slack-bolt==1.20.1`, `python-dotenv==1.0.1`) — check for CVEs manually or add `pip-audit` when a CI pipeline exists.
