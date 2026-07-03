# Commit: Package Changes for Review

Atomic, reviewable commit and PR-ready summary.

## Process
1. Inspect: `git status --short`, `git diff --stat`, `git diff`.
2. Confirm scope: related files only; exclude `venv/`, `.env`, logs, unrelated changes.
3. Run the validation gate from `CONSTITUTION.md` — do not skip.
4. Stage specific files by name, not `git add .` (this repo has `venv/` and `.env` at the root — never stage them).
5. Conventional Commits message: `<type>(<scope>): <imperative description under 72 chars>`, optional body (why/constraints/trade-offs), `Closes #<n>`.
   - Types: feat, fix, refactor, test, docs, chore, perf, style, ci.
6. PR body: summary, changes list, acceptance criteria checkboxes, validation commands run, `Closes #issue`.

## Non-negotiables
Never skip the validation gate; never commit `.env` or secrets; one logical change per commit; PR title matches commit format; no direct push to `main`.
