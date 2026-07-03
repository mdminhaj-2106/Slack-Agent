# Prime: Load Project Context

Start-of-session context loading for the Recorder project (Python / FastAPI / Slack Bolt).

## Steps

1. Run:
   ```bash
   git status --short
   git branch --show-current
   git log -n 8 --oneline
   git remote -v
   ```
2. Confirm stack (should match `CONSTITUTION.md`): Python 3.14, FastAPI, slack-bolt, Socket Mode, no test runner/CI yet.
3. Read durable context in priority order: `CONSTITUTION.md`, `PRD.md`, then all `.claude/reference/*.md` files.
4. Inspect repo shape:
   ```bash
   find . -maxdepth 3 -type f -not -path "./venv/*" -not -path "./.git/*"
   ```
5. Read `main.py` (the sole entrypoint) and any files changed since the last session (`git log -n 5 --stat`). Note: `main.py` raises at import time if Slack env vars aren't set — never `python -c "import main"` without a real `.env`; use `python -m py_compile main.py` for a syntax-only check.
6. Check active plans: `ls .claude/plans/`. Check GitHub context if available: `gh issue list`, `gh pr list`.
7. **Output** a concise context brief: branch, phase (MVP), stack, dirty files, active plan, validation gate, blockers.
