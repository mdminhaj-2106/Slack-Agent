# Implementation Plan: Milestone 2 — Closed-Loop Verifier

## Issue Metadata
- Tracker: GitHub Issue (to be created) — "M2: Closed-loop commitment verifier"
- Priority: Current milestone (M1a + M1b done per milestones.md)
- Owner: Solo build (Saad)
- Branch: `feat/m2-closed-loop-verifier`
- Budget: ~2–3 days (see milestones.md time budget)

---

## Outcome (Testable)
When a commitment pointer is logged to the Canvas (status `open`), the system:
1. Parses the `due_date_hint` already extracted by the M1a classifier.
2. Schedules a background verification job at/after that deadline.
3. At deadline, gathers evidence from Slack (thread history + reactions on the original message).
4. Passes the commitment original text (fetched live, never at rest) + evidence to Gemini for NLI entailment.
5. If entailed → marks the Canvas pointer `kept`, no nudge.
6. If not entailed → sends ONE private DM to the owner with a soft nudge + two buttons: `[✓ Done]` `[↺ Snooze 24h]`.
7. On `[✓ Done]` → marks `kept`. On `[↺ Snooze 24h]` → reschedules +24h. If snooze fires again and still no evidence → marks `overdue`.

**It never posts publicly. It never asks before it searches. Evidence-first, always.**

---

## Critical Constraints From .claude Files

### From CONSTITUTION.md (Non-Negotiable)
- Never store raw Slack message text or LLM-generated summaries at rest.
- Never nudge publicly — only private DM or ephemeral.
- No new libraries without checking `docs/Intitial-research.md`.
- Process messages live via Events API. Never call `conversations.history` / `conversations.replies` in a backfill loop. Our app is internal (Tier 3: ~50+/min, 1,000 objects/request).
- Ack interaction payloads (button clicks) within 3 seconds; do heavy work async.

### From docs/Intitial-research.md
- Verification must use NLI/LLM entailment — check if later messages *satisfy* the commitment.
- Valid evidence signals: later "deployed/merged/done" messages from the owner in the same channel/thread; a ✅ reaction on the original message; a linked PR/closed-ticket URL in the thread.
- Contradiction detection bonus: a later message that explicitly contradicts the commitment → marks `superseded`.
- Use `reactions.get` to check for checkmarks/done emoji on the original message `ts`.

### From architecture.md
- M2 module is planned as `verifier.py` — owns scheduled follow-up, evidence search + NLI entailment, status updates.
- Must not post publicly on behalf of a user.

### From milestones.md (Definition of Done)
- Confirmed commitments get a scheduled follow-up.
- Verification is evidence search + NLI, never "ask the user and take their word for it" as primary signal.
- Only on no evidence found: one private nudge to the owner.
- Pointer record status updates to: `kept / overdue / superseded / forgotten`.

---

## Hard Architectural Decisions

### Decision 1: In-Process Timer (No Persistent Queue)
No database exists. We use `threading.Timer` for scheduling — in-process, no persistence.
If the bot restarts, pending timers are lost. Acceptable for hackathon demo.

**Implication:** The timer is scheduled inside `handlers/actions.py` immediately after a successful Canvas write for `commitment` type pointers.

### Decision 2: Evidence Gathering via conversations.replies (Not RTS)
`assistant.search.context` requires a live `action_token` from a user event payload — unavailable in a headless background timer. Evidence gathering uses:
- `client.conversations_replies(channel=..., ts=...)` — thread replies after capture ts.
- `client.reactions_get(channel=..., timestamp=...)` — emoji reactions on original message.

Both use the bot token directly and are safe at Tier 3 for internal apps.

### Decision 3: Canvas Status Update via sections.lookup + replace
`canvases.sections.lookup` finds the section by searching the Canvas text for the commitment's `ts` value.
`canvases.edit` with `operation: "replace"` rewrites that section's markdown with the updated status field.

### Decision 4: NLI via Existing ai/llm.py (No New AI Library)
Reuse `get_llm()` from `ai/llm.py` with Gemini structured output (`with_structured_output`). No new libraries. Fully aligned with the Gemini-only constraint in CONSTITUTION.md.

### Decision 5: Due Date Parsing via dateparser
The M1a classifier already extracts `due_date_hint` (e.g. "by Friday", "tomorrow EOD").
Use `dateparser` to convert to absolute datetime. Fallback: now + 24h.
`dateparser` is a non-Slack, non-LLM utility library not prohibited by any .claude constraint.

---

## New Files to Create

| File | Owns |
|------|------|
| `ai/due_date.py` | Converts `due_date_hint` string → absolute `datetime` using `dateparser` + 24h fallback |
| `ai/nli.py` | NLI entailment: commitment text + evidence → `NLIVerdict` (kept / superseded / insufficient_evidence) |
| `slack_app/evidence.py` | Fetches thread replies after `ts` + reactions on original message — returns evidence dict, never persists text |
| `slack_app/canvas_updater.py` | Finds Canvas section by pointer `ts` and replaces its status field in-place |
| `handlers/verifier.py` | Orchestration: schedules timer, runs evidence+NLI pipeline, dispatches DM nudge, handles nudge button actions |

## Files to Modify

| File | Change |
|------|--------|
| `handlers/actions.py` | After confirmed Canvas write for `commitment` type: call `schedule_verification()` |
| `handlers/__init__.py` | Add `register_verifier_handlers(slack_app)` for nudge button actions |
| `slack_app/schemas.py` | Add `due_date_hint: Optional[str]` to `PointerRecord` |
| `slack_app/blocks.py` | Add `get_nudge_blocks(owner_id, commitment_permalink)` with `[✓ Done]` + `[↺ Snooze 24h]` buttons |
| `requirements.txt` | Add `dateparser` |
| `.claude/plans/milestones.md` | Append M2 snapshot log when done |
| `.claude/reference/architecture.md` | Mark M2 `verifier.py` row as implemented |
| `.claude/reference/api.md` | Move M2 nudge trigger from Planned to Confirmed |

---

## Module Specifications

### `ai/due_date.py`
**Purpose:** Converts free-text deadline hints to absolute datetimes.
**Function:** `parse_due_datetime(hint: str | None, fallback_hours: int = 24) -> datetime`
**Implementation:**
- Uses `dateparser.parse(hint, settings={"PREFER_DATES_FROM": "future", "RETURN_AS_TIMEZONE_AWARE": True})`.
- If `hint` is `None` or `dateparser` returns `None` → falls back to `datetime.now(UTC) + timedelta(hours=fallback_hours)`.
- If parsed datetime is in the past → uses fallback (prevents immediate firing on stale hints).

---

### `slack_app/evidence.py`
**Purpose:** Gathers post-commitment evidence. Never persists text — only passes in-memory to NLI.
**Function:** `gather_evidence(client, channel_id: str, commitment_ts: str) -> dict`
**Returns:**
```python
{
    "thread_replies": [{"user": str, "text": str, "ts": str}],  # post-commitment only
    "done_reactions": [str]   # names of completion-signal emoji found
}
```
**Implementation:**
- `conversations_replies(channel, ts, oldest=commitment_ts)` — fetches thread replies after the commitment.
- Filters out: the commitment message itself (first item), bot messages (`bot_id` present or `subtype == "bot_message"`).
- `reactions_get(channel, timestamp=commitment_ts)` — extracts reaction names, filtered to done-signal set: `{"white_check_mark", "heavy_check_mark", "done", "✅", "check"}`.
- Returns raw dict — never written to Canvas or persisted anywhere.

**Rate limit:** 2 API calls per job. Internal app Tier 3 = safe.

---

### `ai/nli.py`
**Purpose:** NLI entailment via Gemini structured output.
**Schema:** `NLIVerdict(BaseModel)` — fields: `verdict: str` (one of: `"kept"`, `"superseded"`, `"insufficient_evidence"`), `reasoning_tag: str` (one of: `"done_message"`, `"reaction_signal"`, `"contradiction"`, `"no_signal"`).
**Function:** `evaluate_commitment(commitment_permalink: str, evidence: dict) -> NLIVerdict`

**Prompt design (system):**
```
You are a commitment verifier for an engineering team.
Given a commitment permalink and a set of later messages/reactions from the same thread,
classify whether the commitment has been:
- "kept": later messages clearly show the task was completed (e.g. "done", "deployed", "merged", "shipped", "live", "pushed").
- "superseded": a later message explicitly replaces or cancels the commitment
  (e.g. "we're not doing X anymore", "cancelled", "we decided against it").
- "insufficient_evidence": no clear signal either way.

Rules:
- A ✅ / white_check_mark reaction alone is strong "kept" evidence.
- Only look for explicit completion or cancellation language — do not infer from tone.
- Never fabricate evidence. If in doubt, return "insufficient_evidence".
- reasoning_tag: pick the strongest signal (reaction_signal > done_message > contradiction > no_signal).
```

**Key security constraint:** We pass the `commitment_permalink` to the prompt (not the raw commitment text from memory), plus the evidence texts fetched live. None of this is persisted. The LLM sees text only during the live evaluation call.

---

### `slack_app/canvas_updater.py`
**Purpose:** Updates an existing Canvas pointer's `status` field in-place.
**Function:** `update_pointer_status(client, canvas_id: str, pointer_ts: str, new_status: str) -> bool`
**Implementation:**
1. `canvases_sections_lookup(canvas_id, contains_text=pointer_ts)` — finds the section containing the pointer's unique `ts` value.
2. If no section found → log warning, return `False` (pointer may have been manually deleted).
3. Extract the `section_id` from the response.
4. Rebuild the markdown line with the updated status (same format as `slack_app/formatter.py`, just status field changed).
5. `canvases_edit(canvas_id, changes=[{"operation": "replace", "section_id": section_id, "document_content": {"type": "markdown", "markdown": new_line}}])`.
6. Returns `True` on success, `False` on API failure.

---

### `handlers/verifier.py`
**Purpose:** Orchestration layer — schedules timers, runs the pipeline, dispatches nudges, handles button actions.

**Key functions:**

#### `schedule_verification(client, pointer: PointerRecord)`
- Parses `pointer.due_date_hint` via `ai/due_date.py`.
- Calculates delay in seconds from now to `due_datetime`.
- Fires `threading.Timer(delay_seconds, run_verification, args=(client, pointer))`.
- Logs: `"Verification scheduled for {owner_id}'s commitment at {due_datetime}"`.

#### `run_verification(client, pointer: PointerRecord)`
- Step 1: Gather evidence via `slack_app/evidence.py`.
- Step 2: Evaluate via `ai/nli.py`.
- Step 3a: If `verdict == "kept"` or `verdict == "superseded"` → call `canvas_updater.update_pointer_status(...)` with the verdict as the new status. Log. Done.
- Step 3b: If `verdict == "insufficient_evidence"` → send ONE private DM nudge to `pointer.owner_id` using `client.chat_postMessage(channel=owner_id, ...)` with `get_nudge_blocks(owner_id, pointer.permalink)`. Log.

#### `register_verifier_handlers(slack_app: App)`
Registers two button action handlers:
- `action_id: "commitment_done"` → `ack()` → background thread → update Canvas to `kept`, edit DM to success message.
- `action_id: "commitment_snooze"` → `ack()` → background thread → reschedule +24h timer. On second snooze fire with still no evidence → update Canvas to `overdue`.

---

## Pointer Status Lifecycle

```
[open]         — commitment logged, awaiting verification
   │
   ├─► [kept]        — evidence found by NLI, or owner clicked [✓ Done]
   ├─► [superseded]  — NLI found a later message explicitly cancelling it
   ├─► [overdue]     — snooze expired with no evidence and no user response
   └─► [forgotten]   — future manual dismiss action (out of scope for M2)
```

---

## The Full M2 Execution Flow (Step by Step)

### Step 1 — Capture (no change from M1a)
Alice posts: *"I will set up the CI pipeline by Friday."*
Gemini classifies: `commitment`, `owner_id=U_ALICE`, `due_date_hint="by Friday"`, confidence `0.93`.
Alice clicks `✓ Log`. `handlers/actions.py` writes the PointerRecord to Canvas.

### Step 2 — Schedule (new in M2)
`handlers/actions.py` calls `schedule_verification(client, pointer)`.
`ai/due_date.py` parses `"by Friday"` → next Friday datetime.
`threading.Timer` fires at Friday + a configurable grace period (e.g. +2h to allow EOD work to land).

### Step 3 — Evidence Gathering (new in M2)
Timer fires. `run_verification()` calls `gather_evidence(client, channel_id, ts)`.
Result: `{"thread_replies": [{"user": "U_ALICE", "text": "CI is green on main!", "ts": "..."}], "done_reactions": []}`.

### Step 4 — NLI Evaluation (new in M2)
`evaluate_commitment(pointer.permalink, evidence)` → Gemini evaluates: evidence `"CI is green on main!"` entails `"set up the CI pipeline"`.
Returns `NLIVerdict(verdict="kept", reasoning_tag="done_message")`.

### Step 5a — Clean Close (kept)
`canvas_updater.update_pointer_status(canvas_id, ts, "kept")` rewrites the Canvas line.
No DM sent. Loop closed silently.

### Step 5b — Private Nudge (insufficient_evidence)
`client.chat_postMessage(channel="U_ALICE", blocks=get_nudge_blocks(...))`.
Alice receives a private DM: *"👋 Did 'set up the CI pipeline' land? I couldn't find evidence in the thread."*
`[✓ Done]` `[↺ Snooze 24h]`

### Step 6 — Snooze Handling
Alice clicks `[↺ Snooze 24h]`. Timer reschedules +24h.
After snooze: re-runs evidence check. If still nothing → updates Canvas to `overdue`.

---

## Tests Required (per testing.md)

### Unit Tests (`test_verifier.py`)
| Test | What it covers |
|------|----------------|
| `test_parse_due_datetime_friday` | "by Friday" → next Friday datetime |
| `test_parse_due_datetime_none` | None → now + 24h fallback |
| `test_parse_due_datetime_past_hint` | Past date hint → fallback |
| `test_nli_kept_from_done_message` | Evidence "CI is green" → kept |
| `test_nli_superseded_from_cancel` | Evidence "cancelled" → superseded |
| `test_nli_insufficient_no_replies` | Empty evidence → insufficient_evidence |
| `test_nli_kept_from_reaction` | done_reactions: ["white_check_mark"] → kept |

### Validation Gate
```bash
# Syntax
venv\Scripts\python -m py_compile ai/due_date.py ai/nli.py slack_app/evidence.py slack_app/canvas_updater.py handlers/verifier.py

# Unit tests
venv\Scripts\python test_verifier.py

# Manual smoke test (real workspace)
# 1. python main.py
# 2. Post a commitment in a channel: "I will review the PR by today EOD"
# 3. Click ✓ Log → confirm Canvas pointer written with status "open"
# 4. For demo speed: temporarily set grace period to 60s
# 5. Confirm verification fires → check Canvas → status updates to "kept" or "overdue"
# 6. For nudge path: post commitment with no follow-up → confirm private DM arrives
# 7. Click [✓ Done] → confirm Canvas updates to "kept"
```

---

## Acceptance Criteria (mapped to milestones.md DoD)
- [ ] Commitment pointers with `status: open` trigger a scheduled verification job on confirm.
- [ ] Verification gathers thread replies + reactions without any backfill loop.
- [ ] NLI evaluation uses Gemini structured output — never fabricates or stores text.
- [ ] If evidence is found: Canvas pointer status updates to `kept` or `superseded`. No DM sent.
- [ ] If no evidence: exactly ONE private DM nudge is sent to the owner. Never a public post.
- [ ] `[✓ Done]` DM button → Canvas status `kept`. `[↺ Snooze 24h]` → reschedule. Second snooze fire → `overdue`.
- [ ] Canvas status update uses `canvases.sections.lookup` + `replace` — never duplicates the pointer line.
- [ ] All new files pass `py_compile`. All unit tests pass.
- [ ] Manual smoke test completed in real sandbox workspace.

---

## Risks

| Risk | Mitigation |
|------|------------|
| `threading.Timer` lost on process restart | Acceptable for hackathon. Note in docs. If productionizing: use APScheduler or a persistent queue. |
| Canvas section lookup fails if pointer line was manually edited | `canvas_updater.py` returns `False` and logs warning — does not crash the pipeline. |
| `conversations_replies` returns 0 messages (thread has no replies) | `gather_evidence` returns empty `thread_replies` + reactions only. NLI handles empty gracefully → `insufficient_evidence`. |
| Gemini NLI false positives ("done" used sarcastically) | Confidence is not surfaced to the user — only the verdict enum. False positive = `kept` marked incorrectly. Acceptable for demo precision. Raise in a future iteration. |
| `due_date_hint` is None for commitments without explicit deadlines | `ai/due_date.py` fallback: schedule verification 24h after capture. Configurable. |
| DM nudge fails if bot is not in DM with the user | `chat_postMessage` to a user ID opens a DM channel automatically — this is standard Slack behavior. |
| Canvas write Tier 2 rate limit (20+/min) | Verification jobs are sparse (one per commitment at deadline) — not a bottleneck. |

---

## Implementation Steps (Ordered)

### Step 1 — Install dateparser
```bash
pip install dateparser
# Add to requirements.txt
```

### Step 2 — `ai/due_date.py`
Implement `parse_due_datetime`. Write `test_verifier.py` due-date tests. Validate.

### Step 3 — `slack_app/evidence.py`
Implement `gather_evidence`. No unit test needed (pure API glue — covered by smoke test).

### Step 4 — `ai/nli.py`
Implement `evaluate_commitment` with `NLIVerdict` structured output. Write NLI unit tests.

### Step 5 — `slack_app/canvas_updater.py`
Implement `update_pointer_status`. Manually smoke test against real Canvas.

### Step 6 — `slack_app/blocks.py` (extend)
Add `get_nudge_blocks(owner_id, permalink)`.

### Step 7 — `slack_app/schemas.py` (extend)
Add `due_date_hint: Optional[str]` to `PointerRecord`.

### Step 8 — `handlers/verifier.py`
Implement `schedule_verification`, `run_verification`, `register_verifier_handlers`.

### Step 9 — Wire into existing handlers
`handlers/actions.py`: call `schedule_verification` after Canvas write for commitments.
`handlers/__init__.py`: add `register_verifier_handlers(slack_app)`.

### Step 10 — Validation Gate
Run `py_compile`, unit tests, manual smoke test. Update `.claude` reference files.
