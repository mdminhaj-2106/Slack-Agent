# Init Workspace: Install the AI Workflow Scaffold

Install this same scaffold into another repo without touching its source code.

## Process
1. Detect target repo: `pwd`, `git status`, check for existing `.claude/` scaffold.
2. Detect project type (language, framework, database, test runner, monorepo, package manager, CI, hosting).
3. Create the directory structure (`.claude/commands`, `.claude/skills/*`, `.claude/plans`, `.claude/reference`, `.claude/templates/reference`, `.github/ISSUE_TEMPLATE`).
4. Write scaffold files, skipping any that already exist unless the user asks to overwrite.
5. Adapt `CLAUDE.md` and `CONSTITUTION.md` to the detected project.
6. Run `/create-rules` after installation to fill in evidence-based details.
7. Report installed / skipped / needs-human-review / next-steps.

## Verification checklist
`CLAUDE.md`, `CONSTITUTION.md`, `PRD.md`, `.claude/README.md`, all commands, all skills, all reference docs, GitHub templates.
