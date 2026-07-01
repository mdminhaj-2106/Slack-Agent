# Architecture

## System shape
| Unit | Role | Owns |
|------|------|------|
| `main.py` — `slack_app` | Slack Bolt app | Slack event handling (`app_mention`) |
| `main.py` — `api` | FastAPI app | HTTP surface (`/health`) |
| Background thread | Runs `SocketModeHandler.start()` | The persistent Slack Socket Mode connection |

## Runtime architecture
```mermaid
flowchart TD
  Slack[Slack] -->|Socket Mode event| SocketHandler[SocketModeHandler]
  SocketHandler --> SlackApp[slack_app]
  SlackApp --> MentionHandler[handle_mention]
  MentionHandler -->|say| Slack
  Uvicorn[uvicorn.run] --> FastAPIApp[api]
  FastAPIApp -->|on_startup| BgThread[background thread]
  BgThread --> SocketHandler
  FastAPIApp --> Health[/health/]
```

## Module responsibilities
| Module | Owns | Must not touch |
|--------|------|----------------|
| `main.py` | Bootstrap: env loading, Slack app, FastAPI app, thread startup | Should not grow indefinitely — split into modules (`handlers/`, `detectors/`, `canvas/`) once real detection logic is added |

## Boundary rules
- Secrets load once via `load_dotenv()` at import time; no module should read `os.environ` directly for Slack tokens elsewhere — pull from the already-validated `BOT_TOKEN`/`APP_TOKEN`/`SIGNING_SECRET` constants.
- Slack event handlers must ack/return quickly; long-running work (LLM calls, Canvas writes) must not block the handler thread.

## Critical flows
1. Process boot → `load_dotenv()` → validate tokens → construct `slack_app` → construct `api` → `uvicorn.run`.
2. `on_startup` → spawn daemon thread → `SocketModeHandler(slack_app, APP_TOKEN).start()` (blocks forever in that thread).
3. Slack `app_mention` event → `handle_mention` → log → `say()` reply in-thread.
4. HTTP `GET /health` → `{"status": "ok", "service": "recorder-bot"}`.

## Known architectural risks
- The Socket Mode connection runs in a daemon thread with no supervision — if `handler.start()` raises or the connection drops permanently, nothing restarts it and `/health` will keep reporting fine even though the bot is dead. Add a watchdog before relying on `/health` as a liveness signal for the Slack side.
- `main.py` is a single file; per `docs/Intitial-research.md`, upcoming layers (classifier, Canvas writer, verifier) should live in separate modules rather than being appended here.
