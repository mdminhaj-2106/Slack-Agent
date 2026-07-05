# Implementation Plan: Milestone 1b — `/why` Retrieval via `assistant.search.context`

## Issue metadata
- Tracker: [#7](https://github.com/mdminhaj-2106/Slack-Agent/issues/7) — "M1b: /why retrieval via assistant.search.context"
- Priority: current milestone (M1a done, M1b is next per `.claude/plans/milestones.md`)
- Owner: solo build (Minhaj)
- Branch: `feat/m1b-why-retrieval`

## Outcome (testable)
Mentioning `@Recorder` with a message containing the word "why" (e.g. `@Recorder why did we pick Postgres?`) makes the bot call `assistant.search.context` with that event's `action_token`, and reply in the same thread with a numbered list of ranked permalinks (no message content/snippets, no synthesized summary). Mentioning the bot without "why" gets a one-line usage hint instead of the retired "hello" smoke-test reply.

## Scope
**In:**
- New `handlers/retrieval.py`: registers the `app_mention` listener, detects a "why" query, extracts the topic, calls RTS, formats and posts the reply — all off the main event thread (mirrors the `threading.Thread` pattern already used in `handlers/events.py`).
- Remove the old hardcoded `@slack_app.event("app_mention")` "hello" handler from `main.py` — `retrieval.py` becomes the sole owner of `app_mention`.
- Wire `register_retrieval_handlers` into `handlers/__init__.py` alongside the existing two registrars.

**Out (explicitly deferred, see issue #7):**
- DM (`message.im`) triggering.
- Legacy `search.messages` fallback.
- Pagination (`cursor`) — first page (`limit`) only.
- Any UI beyond plain text (no Block Kit needed here — Block Kit isn't a Canvas constraint, but a plain permalink list is the smallest thing that satisfies the DoD).

## Files to read first
- `.claude/plans/milestones.md` (M1b Definition of Done)
- `CONSTITUTION.md` (evidence-only rule, Slack-specific rules)
- `.claude/reference/architecture.md` (planned module split — confirms `retrieval.py` is the only new module for M1b)
- `handlers/events.py` and `handlers/actions.py` (existing ack-then-background-thread pattern to mirror)
- `main.py` (current `app_mention` handler being replaced)

## Files to change
| File | Change |
|------|--------|
| `handlers/retrieval.py` (new) | `app_mention` listener, why-query detection, RTS call, reply formatting |
| `handlers/__init__.py` | Add `register_retrieval_handlers(slack_app)` call |
| `main.py` | Delete the existing `@slack_app.event("app_mention")` block (lines ~43-59) |
| `.claude/reference/architecture.md` | Mark `retrieval.py` module row as implemented; update flows/known-risks if the RTS call surfaces a new one |
| `.claude/reference/api.md` | Move the M1b row from "Planned Slack-side surface" into a confirmed section once done |
| `.claude/plans/milestones.md` | Append M1b snapshot log entry when done |

## Design notes locked from interrogation
- **Trigger:** `app_mention` only (no DM this milestone).
- **Query detection:** case-insensitive substring match for `"why"` in the mention text (after stripping the `<@BOT_ID>` tag). If absent, don't call RTS — reply with a short usage hint instead. If present, the topic passed to `query` is the mention text with the bot-mention tag stripped (send the whole remaining text as the query, not just the substring after "why" — RTS's own relevance ranking handles the full sentence better than a hand-trimmed fragment).
- **RTS call shape** (confirmed against `docs.slack.dev/reference/methods/assistant.search.context`):
  - `POST assistant.search.context` via `client.api_call("assistant.search.context", json={...})` — the installed `slack_sdk==3.43.0` has no typed wrapper method yet, so this goes through the generic `api_call`, matching the SDK's actual capability rather than assuming a method that isn't there.
  - Params sent: `query` (the stripped mention text), `action_token` (from `event["action_token"]`, top-level per the M0-proven round trip), `channel_types: ["public_channel", "private_channel"]` (matches the scopes actually granted in M0 — no `im`/`mpim` since DM is out of scope and `search:read.im` was never granted), `limit: 10`, `sort: "score"` (default, but explicit for clarity).
  - Response: read `results.messages[]`; each has `permalink`, `channel_name`, `author_name`, `message_ts`. **Never read or forward the `content` field** — that's the raw message snippet, and forwarding it would violate the evidence-only principle even though it's not being persisted (see Non-Negotiable #4 in `CONSTITUTION.md`).
- **Reply format:** plain text, in-thread (`thread_ts=event.get("thread_ts") or event.get("ts")`), top 5 of the returned results, e.g.:
  ```
  Here's what I found on "why did we pick Postgres":
  1. <permalink> — via @author_name in #channel_name
  2. <permalink> — via @author_name in #channel_name
  ```
  Slack will natively unfurl each permalink for the viewer (subject to their own channel access) — Recorder itself never echoes message text.
- **Empty results:** reply with `"No matching evidence found for '<topic>' yet."` — don't silently no-op (a silent bot reads as broken, not empty).

## Implementation steps

### Step 1 — `handlers/retrieval.py`
**What:** New module with three pieces:
1. `extract_why_query(text: str) -> str | None` — strips the `<@...>` mention tag, returns the remaining stripped text if it contains "why" (case-insensitive), else `None`.
2. `run_search_and_reply(client, say, action_token, query, thread_ts)` — background-thread target. Calls `client.api_call("assistant.search.context", json={...})`, handles `ok: False`/exceptions/empty results, formats the top 5 into the reply text above, calls `say(text=..., thread_ts=thread_ts)`.
3. `register_retrieval_handlers(slack_app)` — registers `@slack_app.event("app_mention")`; on each event, calls `extract_why_query`; if `None`, `say()` the usage hint synchronously (cheap, no thread needed, mirrors `handle_dismiss` in `handlers/actions.py`); if a query, spawn a daemon `threading.Thread` running `run_search_and_reply` (mirrors `handlers/events.py`'s `process_message_async` pattern) and return immediately.

**Files:** `handlers/retrieval.py`

**Validation:** `python -m py_compile handlers/retrieval.py`; unit test per Step 3.

### Step 2 — Wire registration
**What:** In `handlers/__init__.py`, import and call `register_retrieval_handlers(slack_app)` next to the other two registrars. In `main.py`, delete the standalone `@slack_app.event("app_mention") def handle_mention(...)` block — `retrieval.py` is now the only `app_mention` owner (Bolt would otherwise fire both listeners on every mention, double-replying).

**Files:** `handlers/__init__.py`, `main.py`

**Validation:** `python -m py_compile main.py handlers/__init__.py handlers/retrieval.py`.

### Step 3 — Test: query detection
**What:** Add `test_retrieval.py` (colocated, per `.claude/reference/testing.md` — no framework exists yet, so use bare `assert`s in a `if __name__ == "__main__":` block, consistent with "unit tests proportional to risk" and this being the one piece of new branching logic worth a regression check). Cover:
- `"<@U123> why did we pick Postgres?"` → returns `"did we pick Postgres?"` (or the full stripped text, matching whatever exact stripping the function does — assert the literal output, not just "is not None").
- `"<@U123> hello there"` → returns `None`.
- `"<@U123> WHY is this blocked"` → case-insensitive match still works.

**Files:** `test_retrieval.py`

**Validation:** `python test_retrieval.py` exits 0.

### Step 4 — Manual smoke test (real workspace, per `.claude/reference/testing.md` — no Slack mock exists)
**What:**
1. `python main.py` with real `.env`.
2. In the sandbox workspace, `@Recorder why did we decide X` in a channel where a matching message exists → confirm a permalink reply appears in-thread, and manually confirm the permalink resolves to the right message.
3. `@Recorder hello` (no "why") → confirm the usage-hint reply, not a crash or the old "hello" text.
4. `@Recorder why blah blah nonsense topic` (no matches expected) → confirm the "No matching evidence found" reply, not a silent failure.
5. If a second workspace user (without access to the source channel) can be tested, confirm they don't get a permalink they can't open — this is the one DoD line that can't be verified by reading code, only by testing live per the milestone's own instruction ("verify it in testing, don't assume").

**Files:** none (manual)

## Tests and validation gate
```bash
python -m py_compile main.py handlers/__init__.py handlers/retrieval.py   # syntax
python test_retrieval.py                                                  # query-detection unit test
python main.py                                                            # manual smoke test, real .env — see Step 4
```

## Acceptance criteria
- [ ] `@Recorder why <topic>` in a channel with matching history returns a ranked, in-thread permalink list.
- [ ] `@Recorder <no "why">` returns a usage hint, not a crash and not the old "hello" reply.
- [ ] A query with no RTS matches returns an explicit "no evidence found" reply, not silence.
- [ ] The reply never contains the `content`/snippet field from the RTS response — permalinks (+ author/channel metadata) only.
- [ ] `action_token` is read from the `app_mention` event and passed to `assistant.search.context`; the call is never attempted with a bare bot token alone.
- [ ] `handlers/retrieval.py` is the sole registrant of `app_mention` (old `main.py` handler removed, no double replies).
- [ ] `python -m py_compile` passes on all changed files; `python test_retrieval.py` passes; manual `@mention` smoke test done in the real sandbox workspace.
- [ ] `.claude/reference/architecture.md`, `.claude/reference/api.md`, and `.claude/plans/milestones.md` updated to reflect M1b done.

## Risks
- **`action_token` missing or expired:** if absent from the event dict, log and reply with a generic "can't search right now, try mentioning me again" rather than raising — RTS is architecturally unusable without it, this isn't recoverable mid-request.
- **`slack_sdk` has no typed wrapper for `assistant.search.context`:** using raw `client.api_call(...)` works but isn't validated by the SDK's type layer — a typo in a param name fails at runtime, not at lint time. Mitigated by the manual smoke test in Step 4.
- **Rate limit:** RTS is Tier 2 (20+/min per `docs/Intitial-research.md`) — a single mention-triggered call per query is nowhere near this, no throttling needed at this scale.
- **Scope mismatch:** Slack's own docs list bot-token required scopes as `search:read.files`, `search:read.public`, `search:read.users` — different from what M0's snapshot log says was granted (`search:read.public` + `search:read.private`). The M0 round trip already proved `ok: true` empirically, so trust that over the docs; but if private-channel results come back empty in Step 4's smoke test, re-check granted scopes in the sandbox app config before debugging the code.
- **Unknown:** whether the sandbox's RTS index has ingested messages fast enough for same-session testing (RTS indexing latency isn't documented) — if a just-posted test message doesn't show up in search immediately, wait and retry before assuming a bug.
