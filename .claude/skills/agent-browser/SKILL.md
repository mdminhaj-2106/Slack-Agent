---
name: agent-browser
description: Verify web UI behavior in a browser — responsive layout, forms, state transitions, and critical user flows.
---

## What to verify
Page loads without console errors, main flows functional at all viewports, no text overflow, form validation errors visible, loading/empty/error/success states all correct, keyboard accessible.

## Standard viewports
375×812 (mobile), 768×1024 (tablet), 1440×900 (desktop).

## Critical journeys
> Fill from PRD.md by running /create-rules. This project currently has no web UI — Recorder is a Slack bot with only a `/health` HTTP endpoint. Revisit this skill once a dashboard or admin UI is added.

## Evidence format
Browser+viewport checked, pages/flows verified, states verified, known gaps, screenshots for non-trivial changes.

## When to use
After any page/layout/component/CSS change, new routes, data-loading changes, before release.
