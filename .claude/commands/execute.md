# Execute: Implement a Prepared Plan

Implement faithfully, scoped and tested.

## Before starting
Read the plan, read `CONSTITUTION.md` (architecture + validation gate), read all "Files to Read First", run `git status` to preserve unrelated changes.

## Process
Implement steps in order; re-read a file before editing it; run each step's validation; add/update tests for behavior changes (once a test runner exists — currently none); update `.claude/reference/` for contract changes (new Slack scopes, new event handlers, new Canvas fields).

## Editing rules
Narrow edits only. No new libraries without checking `CONSTITUTION.md`/`docs/Intitial-research.md` first. Keep Slack event-handling logic out of `main.py` as it grows — split into modules per concern (classifier, Canvas writer, verifier) rather than one growing file. Match existing conventions (plain functions, module-level app objects, `logger.info` for tracing).

## Validation gate
Current gate:
```bash
python -m py_compile main.py   # syntax check only — `import main` would fail without .env set (module raises if Slack tokens are missing)
python main.py                 # manual smoke test with real .env
```
Once a lint/test tool is added, update this section and `CONSTITUTION.md` together.

For UI changes: N/A — no frontend in this project yet.

## Completion report
Files changed, behavior implemented, commands run, commands skipped (with reason), open gaps, PR/issue status.
