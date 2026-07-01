# Plan Feature: Issue to Implementation Plan

Convert a GitHub issue or feature description into an executable plan. No code during this step.

## Inputs
GitHub issue number (`gh issue view <n>`), or a plain description with acceptance criteria. Also: target area (e.g. "classifier", "Canvas", "verifier"), priority, constraints.

## Planning process
1. Read `CONSTITUTION.md` and the relevant `.claude/reference/` file for the target area.
2. Fetch issue details; extract acceptance criteria.
3. Investigate the codebase: `main.py` is currently the only module — identify where new logic should live (e.g. a new `handlers/` or `detectors/` module, not more code crammed into `main.py`). Check `docs/Intitial-research.md` for the intended technical approach (which Slack API, which library, which rate-limit constraint applies).
4. Design: atomic steps, each with what/files/validation; edge cases (Slack API errors, `action_token` missing, `trigger_id` expiry, empty detection results); required tests.
5. Write the plan to `.claude/plans/<identifier>-<kebab-title>.md`.

## Plan template
Issue metadata (tracker/priority/owner/branch), outcome (testable, not aspirational), scope (in/out), files to read first, files to change, implementation steps (what/files/validation each), tests and validation gate, acceptance criteria checkboxes, risks (Slack rate limits, `action_token` availability, Canvas size limits, unknowns).
