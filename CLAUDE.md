# CLAUDE.md — Claude Code Session Bootstrap

## Start Every Session By Reading

1. `CONSTITUTION.md`
2. `.claude/reference/architecture.md`
3. `.claude/reference/api.md`
4. `.claude/reference/testing.md`
5. Active `.claude/plans/*.md`

Then run:
```bash
git status --short
git branch --show-current
gh issue list --limit 10
```

## Quick Commands

```bash
# Install:   pip install -r requirements.txt
# Dev:       python main.py            # runs FastAPI + Slack Socket Mode
# Lint:      (none configured yet)
# Test:      (none configured yet)
```

## Pre-Commit Checklist

- [ ] Syntax check passes (`python -m py_compile main.py`)
- [ ] Build/run passes (`python main.py` starts without error, real `.env` present)
- [ ] Tests pass (once a test runner exists)
- [ ] No secrets committed (`.env` stays untracked)
- [ ] Scope matches the issue — nothing more
- [ ] .claude/reference/ updated if contracts changed

## Agent Rules (Summary)

Full rules in CONSTITUTION.md. Key non-negotiables:
- Recorder stores only evidence pointers (permalink + ts + channel id) in the Canvas — never raw message text or synthesized summaries.
- Build as an internal Slack app; never architect around bulk `conversations.history` pulls (Tier 1 rate limit for non-internal apps).
- Ack Slack interaction payloads within 3 seconds; do slow work (LLM calls) async.
- Never commit `.env` or real Slack tokens.
