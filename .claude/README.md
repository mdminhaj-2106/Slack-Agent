# AI Workflow Scaffold

This directory contains the AI-agent workflow scaffold for Recorder (Slack decision/commitment capture agent).

## Directory Structure

```text
.claude/
  README.md                          — this file
  commands/
    prime.md                         — start-of-session context loading
    create-rules.md                  — generate/refresh CONSTITUTION.md
    create-prd.md                    — create product requirements document
    plan-feature.md                  — convert issue to implementation plan
    execute.md                       — implement a prepared plan
    commit.md                        — package changes for review
    init-workspace.md                — install scaffold into another repo
  skills/
    agent-browser/SKILL.md           — browser UI verification (no UI yet — placeholder)
    e2e-test/SKILL.md                — end-to-end journey testing
    debug/SKILL.md                   — systematic debugging workflow
  plans/                             — feature implementation plans
  reference/                         — live project technical docs
    architecture.md
    api.md
    testing.md
    deployment.md
    security.md
  templates/                         — blank templates for reference docs
    PRD-template.md
    reference/
      architecture-template.md
      api-template.md
      database-template.md
      testing-template.md
      deployment-template.md
      security-template.md
```

No `database.md` yet — no database/ORM exists in this project. Add it (from `templates/reference/database-template.md`) once one is introduced.

## Daily Workflow

```text
Start session   → /prime
Pick work       → select GitHub issue in Ready or In Progress
Plan            → /plan-feature (for non-trivial work)
Implement       → /execute
Verify          → run validation gate from CONSTITUTION.md
Debug           → /debug (when something breaks)
E2E check       → /e2e-test (before release or risky merge)
Commit + PR     → /commit
```

## Command Reference

| Command | When to use |
| ------- | ----------- |
| `/prime` | Starting a session or switching context |
| `/create-rules` | Rebuilding CONSTITUTION.md from changed codebase |
| `/create-prd` | Turning product decisions into a durable PRD |
| `/plan-feature` | Breaking a GitHub issue into steps |
| `/execute` | Implementing a prepared plan |
| `/commit` | Packaging changes into an atomic commit |
| `/debug` | Diagnosing a bug systematically |
| `/agent-browser` | Verifying UI (once a web UI exists) |
| `/e2e-test` | Running complete journey tests |
| `/init-workspace` | Installing this scaffold into another repo |
