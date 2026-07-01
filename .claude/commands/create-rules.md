# Create Rules: Generate or Refresh CONSTITUTION.md

Regenerate `CONSTITUTION.md` from codebase evidence — no guessing.

## Steps

1. Inventory the repo: `find . -maxdepth 3 -type f -not -path "./venv/*" -not -path "./.git/*"`.
2. Detect the full stack: language/runtime (check `requirements.txt`, any lock file), web framework (FastAPI), Slack SDK (slack-bolt, Socket Mode vs HTTP), test runner (grep for `pytest`/`unittest` usage), CI (`.github/workflows/`), hosting (Dockerfile/fly.toml/etc.).
3. Read representative source: `main.py` (currently the only source file), and any new modules added since this doc was last written.
4. Read CI config (if any) to extract the exact validation command sequence — currently none exists, so the validation gate stays manual (`python main.py` smoke test) until one is added.
5. Extract rules: architecture layers, Slack event-handling conventions, storage rules (evidence-only Canvas per `docs/Intitial-research.md`), GitHub workflow.
6. Rewrite `CONSTITUTION.md` using the existing structure, with concrete evidence-based content. Write `UNKNOWN` for anything genuinely unclear — never a placeholder.
7. **Output:** detected stack with evidence file per decision, sections updated, unknowns list.
