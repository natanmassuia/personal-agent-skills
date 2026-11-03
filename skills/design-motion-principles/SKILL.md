---
name: design-motion-principles
description: Create or audit web/UI motion and animation with purpose, restraint, and accessibility. Use when building interactive components with motion (React/Framer Motion/CSS), or when asked to "review my animations", "audit motion", "add motion", or check transitions against taste and performance. Applies three design-engineer lenses (Emil Kowalski, Jakub Krehel, Jhey Tompkins) weighted by project type.
compatibility: Claude Code, Codex/Cline/Roo, OpenCode, Antigravity (any agent that can read reference files and run the two workflows)
---

# Design Motion Principles

Build and review motion that earns its place. Two modes, three designer perspectives, one hard rule: `prefers-reduced-motion` is always respected.

## Purpose

Give motion work the judgment of experienced design engineers instead of adding animation by reflex. The skill carries each designer's philosophy as a reference lens and routes every task through a workflow that reads context first, then generates or audits against a shared cookbook.

- **Create mode** — build an interactive component with purposeful motion. Workflow: `workflows/create.md`.
- **Audit mode** — review existing motion and produce a per-designer report (HTML by default, terminal on request). Workflow: `workflows/audit.md`.

## The three lenses

| Designer | Reference | Emphasis |
|---|---|---|
| Emil Kowalski | `references/emil-kowalski.md` | Restraint, speed, purpose — knowing *when not to animate* |
| Jakub Krehel | `references/jakub-krehel.md` | Invisible enhancement — subtle polish for repeated production use |
| Jhey Tompkins | `references/jhey-tompkins.md` | Playful experimentation — creative CSS and easing personality |

## Context-to-Perspective Mapping

Infer project type, then weight a primary and secondary lens before generating or auditing. Confirm the weighting with the user (one short block) when it is genuinely ambiguous.

| Project type | Primary | Secondary |
|---|---|---|
| Productivity SaaS, dashboard, internal tool | Emil | Jakub |
| Client production app, e-commerce, fintech | Jakub | Emil |
| Marketing site, landing page, portfolio | Jhey | Emil |
| Creative, playful, kids, brand experiment | Jhey | Jakub |
| Unclear / general UI | Emil | Jakub |

## Rules

- `prefers-reduced-motion` support is mandatory in everything generated or passed by an audit (`references/accessibility.md`).
- All motion code comes from `references/motion-cookbook.md` — do not hand-roll ad-hoc values.
- Flag AI-slop motion and anti-patterns from `references/anti-checklist.md`; self-check generated code against `references/creation-gotchas.md`.
- Respect existing project conventions (durations, easing, libraries) found in `CLAUDE.md`, `package.json`, and current components.
- Never animate for its own sake — if motion adds no clarity or feedback, leave it out.

## Process

1. Pick the mode: create or audit.
2. Read the required files listed at the top of the chosen workflow (not everything upfront).
3. Infer project context and propose a primary/secondary weighting from the mapping table; confirm if ambiguous.
4. Run the workflow steps in order.
5. Produce the output in the required format.

## Output

- **Create mode:** component code built against the cookbook, with reduced-motion handling and a short note on the weighting applied.
- **Audit mode:** a per-lens report. Default is a self-contained `.html` file in the project's `motion-audits/` with auto-looping demo cards per finding; terminal/inline markdown when the user asks (`--terminal`, `--inline`, "show it inline"). Format defined in `references/output-format.md`.
