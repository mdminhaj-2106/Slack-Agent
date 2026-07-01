# Testing

## Quality gates
No automated test runner is configured yet. Current gate is manual:
```bash
python -c "import main"   # import sanity check
python main.py             # manual smoke test: /health + real @mention in Slack
```

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

## Critical journeys (from PRD.md)
| Journey | Must cover |
|---------|-----------|
| `@mention` → reply | Bot responds in-thread with the mentioning user tagged |
| `/health` | Returns 200 + `{"status": "ok"}` |
| (future) decision capture confirm | Ephemeral prompt fires only for the author, one-tap confirm writes exactly one pointer |
| (future) `/why` retrieval | Only returns permalinks the querying user actually has access to |

## What must have tests
Any commitment/decision classifier logic (false positives/negatives directly affect user trust), the Canvas pointer schema (must never include raw message text), the verification loop (kept/overdue/superseded logic).

## What does not need tests
Bootstrap/wiring code (`load_dotenv`, thread spawning) — covered by the manual smoke test; trivial `/health` endpoint.

## PR verification format
State which of the above commands were run and their result; for anything Slack-facing, confirm a real `@mention` was tested in a workspace (no Slack sandbox/mock exists yet).
