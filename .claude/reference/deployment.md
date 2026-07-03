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
Not yet defined. A free Slack Developer Program sandbox already exists (internal app, unlocks paid Enterprise Grid features for testing) but is **not yet configured** — Agents & AI Apps feature and `search:read.*` scopes still need to be enabled/granted (M0, see `PRD.md` Roadmap). No production deploy target has been chosen yet — out of scope for the 10-day hackathon build.

## Environment variables
| Var | Purpose | Required |
|-----|---------|----------|
| `SLACK_BOT_TOKEN` | Bot token (`xoxb-...`) for API calls | Yes |
| `SLACK_APP_TOKEN` | App-level token (`xapp-...`) for Socket Mode | Yes |
| `SLACK_SIGNING_SECRET` | Validates requests came from Slack | Yes |
| `GEMINI_API_KEY` | Google Gemini API key — powers the decision/commitment classifier | From M1a onward |

`.env.example` lists all four (fixed — previously only listed `SLACK_BOT_TOKEN`).

## Health checks
`GET /health` — process liveness only (does not currently reflect Slack Socket Mode connection state — see `architecture.md` risks).

## Rollback procedure
UNKNOWN — no deploy pipeline exists yet.

## Secrets management
`.env` (gitignored) locally. No secrets manager integrated yet — needed before any shared/production deploy.

## Monitoring
None configured. Currently only `logger.info` to stdout.
