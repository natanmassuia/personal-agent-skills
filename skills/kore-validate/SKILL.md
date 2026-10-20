---
name: kore-validate
description: Progressive validation scaled to risk
compatibility: opencode, claude, codex
---
# KORE VALIDATE
- Tier 1 (edit): run ONLY the affected test file or case, e.g. `npm --prefix <module> run test -- <file>`.
- Tier 2 (feature): `npm --prefix <module> run typecheck` and the build of the affected module only.
- Tier 3 (full suite, all modules): NEVER unless explicitly commanded.

A failure outside the touched module is pre-existing until proven otherwise: report it, do not fix it, do not hide it.
