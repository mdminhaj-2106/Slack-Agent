# Testing

## Quality gates
No automated test runner is configured yet. Current gate is manual:
```bash
python -m py_compile main.py   # syntax check only — safe without .env
python main.py                  # manual smoke test with real .env: /health + real @mention in Slack
```
(`import main` — not `python -c "import main"` — raises without a real `.env`, since module-level code validates Slack tokens at import time; use `py_compile` for a no-`.env` syntax check.)

## Test layers
| Layer | Status |
|-------|--------|
| Unit | none yet |
| Integration (Slack event → handler) | none yet |
| E2E (real Slack workspace) | manual only |

## File conventions
None established yet. When a test runner is added (recommend `pytest` — stdlib-adjacent, zero new concepts beyond what's needed), use `test_*.py` files colocated or in a `tests/` dir, matching whichever convention the first test-writing PR sets.

## Test data rules
No database exists yet — nothing to seed/fixture. Slack event payloads for handler tests should be minimal dicts matching the real event shape (see Slack Bolt event docs), not full recorded payloads.

## Critical journeys (from PRD.md — tagged by milestone)
| Journey | Milestone | Must cover |
|---------|-----------|-----------|
| `@mention` → reply | done | Bot responds in-thread with the mentioning user tagged |
| `/health` | done | Returns 200 + `{"status": "ok"}` |
| `action_token` → `assistant.search.context` | M0 | One proven round-trip call succeeds before M1b starts |
| Decision/commitment capture confirm | M1a | Ephemeral prompt fires only for the author; one-tap confirm writes exactly one pointer; dismiss writes nothing |
| Canvas pointer write | M1a | Never contains raw message text or an LLM-generated sentence — permalink/ts/channel/type/owner/confidence only |
| `/why` retrieval | M1b | Only returns permalinks the querying user actually has access to; triggered via `app_mention`/DM, not a slash command |
| Commitment verification | M2 | Kept/overdue/superseded/forgotten status is only set from evidence search + NLI, never from a user claim alone |

## What must have tests
Any commitment/decision classifier logic (false positives/negatives directly affect user trust), the Canvas pointer schema (must never include raw message text), the verification loop (kept/overdue/superseded logic).

## What does not need tests
Bootstrap/wiring code (`load_dotenv`, thread spawning) — covered by the manual smoke test; trivial `/health` endpoint.

## PR verification format
State which of the above commands were run and their result; for anything Slack-facing, confirm a real `@mention` was tested in a workspace (no Slack sandbox/mock exists yet).
