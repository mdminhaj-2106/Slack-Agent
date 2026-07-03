# Recorder — Milestone Plan

Build context: hackathon submission, **10-day budget** (started 2026-07-02). LLM: **Google Gemini**. Slack workspace: Dev Program sandbox exists, **not yet configured** for Agents & AI Apps / RTS.

Full scope/rationale: `docs/Intitial-research.md`. Product contract: `PRD.md`. This file tracks live status — update the Snapshot line under a milestone whenever its state changes; don't rewrite history, append.

Rule: work the milestones in order. Never start a later milestone's code before the current one's Definition of Done is met — see `CONSTITUTION.md` Code Rules.

---

## M0 — Platform de-risk
**Status: done**

Definition of done:
- Agents & AI Apps feature enabled on the sandbox app.
- Granular scopes granted: `search:read.public`, `search:read.private` (add `search:read.im` only if DM search is actually needed).
- One proven round-trip: an `app_mention` event yields an `action_token`, and a test call to `assistant.search.context` using that token succeeds.

Why this is first: `/why` (M1b) is architecturally dead without this. Finding out RTS doesn't work on day 9 is a demo-killing risk; finding out on day 1 is a Tuesday.

Snapshot log:
- 2026-07-02 — Not started. Sandbox exists, feature/scopes unconfigured.
- 2026-07-02 — Done. Agents & AI Apps enabled, search:read.public + search:read.private granted, reinstalled. Round-trip proven: `event["action_token"]` (top-level on the app_mention event dict) passed to `assistant.search.context` returned `ok=True`. M1b can rely on this shape.

---

## M1a — Capture (**the real MVP**)
**Status: done** — blocked by nothing (can start in parallel with M0 for the classifier/confirm plumbing, but the Canvas write and full loop don't need RTS at all)

Definition of done:
- Gemini classifier: given a Slack message, returns decision/commitment/none + confidence.
- On high-confidence hit, an ephemeral Block Kit message posts in-thread (if the message is already a reply in an active thread) or as a plain channel ephemeral otherwise, visible only to the author, with ✓ Log / ✗ Dismiss buttons. Slack silently drops ephemeral replies threaded onto a `ts` with zero real replies — never force-thread a fresh top-level message.
- On ✓, exactly one pointer record is written to the Canvas: `channel_id`, `ts`, permalink, detected type, owner `user_id`, confidence, status. Never raw message text, never an LLM-generated sentence.
- On ✗, nothing is written.
- Interaction payload acked within 3 seconds; classification/Canvas write happen after the ack, not before.

Why this is the MVP, not the old starter: this is the first point where the actual novel loop (passive detect → in-flow confirm → evidence-only store) is real and demoable on its own, even with no retrieval yet.

Snapshot log:
- 2026-07-02 — Not started.
- 2026-07-03 — Done. Implemented LangGraph + LangChain structured classification, ephemeral Block Kit confirm/dismiss actions, and secure Canvas pointer writes. Configured with a dedicated config.py settings class and modular root handlers/, slack/, and ai/ folders. All compilation checks pass.


---

## M1b — Retrieval
**Status: not started** — blocked by M0

Definition of done:
- `/why [topic]` works when triggered via `app_mention` or DM to the bot (not a slash command — no `action_token` there).
- Query goes through `assistant.search.context` using the `action_token` from that event.
- Response is ranked permalinks, pulled live — Recorder never caches or re-serves message text.
- Only returns results the querying user actually has access to (RTS respects this natively via granular scopes — verify it in testing, don't assume).

Snapshot log:
- 2026-07-02 — Not started.

---

## M2 — Closed-loop verifier
**Status: not started** — blocked by M1a (needs confirmed commitments to verify)

Definition of done:
- Confirmed commitments get a scheduled follow-up at/after their due signal.
- Verification is evidence search + NLI entailment against later messages — never "ask the user and take their word for it" as the primary signal.
- Only on no evidence found: one private nudge to the owner (DM or ephemeral), never a public post.
- Pointer record status updates to kept / overdue / superseded / forgotten.

Snapshot log:
- 2026-07-02 — Not started.

---

## M3 — Passive intelligence (stretch, pick exactly one)
**Status: not started** — only attempt with days to spare after M2

Candidates (pick the cheapest given what M1/M2 already built, don't attempt more than one):
- Repeat-question clustering (embeddings + cosine similarity).
- Bus-factor heuristic (thread-participation concentration).
- Contradiction detector (similarity-retrieve → NLI check).

Snapshot log:
- 2026-07-02 — Not started, not yet decided which candidate.

---

## Time budget check-in
Re-evaluate this table whenever a milestone closes — if actuals are trending over estimate, cut M3 first, then narrow M2's scope (e.g. verifier without scheduling, evidence-check-on-demand only) before ever cutting into M1a/M1b.

| Milestone | Est. | Actual | Notes |
|-----------|------|--------|-------|
| M0 | ~1 day | — | |
| M1a | ~2–3 days | — | |
| M1b | ~1–2 days | — | |
| M2 | ~2–3 days | — | |
| M3 | remainder | — | |
