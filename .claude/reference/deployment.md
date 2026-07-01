# Deployment

## Environments
| Env | Status |
|-----|--------|
| Local | Only environment currently set up (`venv/` + `.env`) |
| Staging | UNKNOWN — not yet set up |
| Production | UNKNOWN — not yet set up |

## Stack
- Hosting: UNKNOWN — no Dockerfile, fly.toml, vercel.json, or render.yaml present.
- Container: none.
- Process: `python main.py` runs uvicorn + a background Socket Mode thread in one process.

## Deploy process
Not yet defined. Per `docs/Intitial-research.md`, the recommended path for continued development is a free Slack Developer Program sandbox (internal app, unlocks paid Enterprise Grid features for testing). No production deploy target has been chosen yet.

## Environment variables
| Var | Purpose | Required |
|-----|---------|----------|
| `SLACK_BOT_TOKEN` | Bot token (`xoxb-...`) for API calls | Yes |
| `SLACK_APP_TOKEN` | App-level token (`xapp-...`) for Socket Mode | Yes |
| `SLACK_SIGNING_SECRET` | Validates requests came from Slack | Yes |

Note: `.env.example` currently only lists `SLACK_BOT_TOKEN` — it's missing `SLACK_APP_TOKEN` and `SLACK_SIGNING_SECRET`, both of which `main.py` requires. Worth fixing in a follow-up.

## Health checks
`GET /health` — process liveness only (does not currently reflect Slack Socket Mode connection state — see `architecture.md` risks).

## Rollback procedure
UNKNOWN — no deploy pipeline exists yet.

## Secrets management
`.env` (gitignored) locally. No secrets manager integrated yet — needed before any shared/production deploy.

## Monitoring
None configured. Currently only `logger.info` to stdout.
