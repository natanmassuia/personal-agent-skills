---
name: kore-guardrails
description: Install a PreToolUse hook that blocks destructive git, database-altering and secret-printing shell commands before the agent runs them. Use when setting up an agent workspace or a VPS agent.
compatibility: claude
---

# Kore guardrails

Derived from `git-guardrails-claude-code` (Matt Pocock, MIT). No `jq` needed: the hook matches the raw tool-call JSON, so it never fails open when `jq` is missing.

## Blocked

- Git: `push`, `reset --hard`, `clean -f`, `branch -D`, `checkout .`, `restore .`
- Database: `prisma migrate`, `prisma db push|execute`, `db:migrate`, `db:seed`, `DROP TABLE|DATABASE`, `TRUNCATE`
- Secrets: `cat|type|more|less|head|tail` on `.env*`, `printenv`, bare `env`, `Get-Content ... .env`

## Install (project scope)

1. Copy `scripts/block-dangerous.sh` to `.claude/hooks/block-dangerous.sh`.
2. Merge into `.claude/settings.json` (keep existing keys):

```json
{ "hooks": { "PreToolUse": [ { "matcher": "Bash",
  "hooks": [ { "type": "command", "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-dangerous.sh\"" } ] } ] } }
```

3. Verify: `echo '{"tool_input":{"command":"git push origin main"}}' | bash .claude/hooks/block-dangerous.sh` must exit 2 with `BLOCKED`.

A blocked command means the user must run it. Do not look for a workaround.
