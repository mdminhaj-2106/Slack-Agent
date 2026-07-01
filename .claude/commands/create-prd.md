# Create PRD: Product Requirements Document

Turn product intent into a buildable, sprint-ready PRD at `PRD.md`.

## Required sections
Executive summary (product/users/problem/MVP success), principles (3–5 guiding decisions), users table (role/goal/pain), MVP scope (explicit in/out), functional requirements with acceptance criteria, system architecture with a Mermaid diagram, API/data contracts (Slack event payloads, Canvas pointer schema), security/auth notes (Slack scopes, `action_token` handling), success metrics, phased roadmap table, risks table, GitHub collaboration model.

## Rules
- Concrete acceptance criteria over vague descriptions.
- Separate MVP (current starter bot) from later phases (classifier, Canvas, verifier — see `docs/Intitial-research.md`).
- Mermaid only when it clarifies flow.
- Update `.claude/reference/` when the PRD changes contracts (e.g. new Slack scopes, new API endpoints).
- Every section should map to actionable GitHub issues.

Source material: `docs/Intitial-research.md` already contains the full product/UX/architecture research — pull from it rather than re-deriving.
