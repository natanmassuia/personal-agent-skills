---
name: kore-fix
description: Small focused fixes using targeted inspection
compatibility: opencode, claude, codex
---
# KORE FIX
1. `git status --short`. Know what is already dirty; never touch unrelated changes.
2. Locate the failure precisely (exact error text or symbol via Grep). NO full-repo scans.
3. Edit the minimum blast radius. No refactors, renames or new abstractions.
4. Validate per `kore-validate` Tier 1 only.
5. `git diff --stat`, then report per `kore-report`.

- If the repo ships `scripts/agent-status.mjs`, `agent-test.mjs`, `agent-diff-summary.mjs`, prefer them over the raw commands.
- Two failed attempts on the same step: STOP and report. Do not widen the fix.
