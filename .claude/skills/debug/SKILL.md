---
name: debug
description: Systematic debugging workflow for diagnosing errors, unexpected behavior, and performance regressions across any stack.
---

## Steps
1. **Reproduce** — confirm exact error/behavior, minimum trigger conditions, deterministic vs intermittent. Check for regression with `git log`.
2. **Read the error** — Python tracebacks: start from the bottom (innermost cause), find file+line. For silent wrong behavior (e.g. bot not replying): check `logger.info` output first (`main.py` already logs on mention).
3. **Check recent changes** — `git log -n 15 -- main.py` and `git diff HEAD~3 -- main.py` (or whichever file is implicated).
4. **Hypothesize** — 2–3 concrete ranked hypotheses with the cheapest test for each. Do not fix without a hypothesis.
5. **Test** — targeted logging or a minimal repro (e.g. a standalone script hitting the Slack SDK directly). Never delete production code just to see if the bug goes away.
6. **Fix** — change only what evidence points to; run the validation gate; remove debugging logs.
7. **Write a regression check** — even a small `assert`-based script that fails on unfixed code, passes on fixed code, given there's no test framework yet.
8. **Confirm** — reproduce the original scenario fixed.

## Common patterns for this stack
- **Slack Bolt**: bot not responding to mentions → check `app_mentions:read` scope, check Socket Mode connection didn't die silently (look for reconnect logs), check `SLACK_APP_TOKEN` vs `SLACK_BOT_TOKEN` mixup.
- **FastAPI/uvicorn**: `/health` unreachable → check the background thread didn't crash and take the process down with it (it's a daemon thread — an unhandled exception in `start_slack_socket_mode` won't crash `uvicorn` but will silently kill the Slack connection).
- **Python generally**: `AttributeError`/`KeyError` on Slack event payloads — Slack event shapes vary by event type; use `.get()` with defaults (already the pattern in `handle_mention`), never direct indexing.
- **Rate limits**: a `429` from any Slack API call — check whether the call is `conversations.history`/`replies` (Tier 1 for this app type — see `CONSTITUTION.md`) before adding retry logic; the fix may be "don't call this API this way," not "retry harder."
