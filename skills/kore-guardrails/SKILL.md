---
name: kore-guardrails
description: Install a PreToolUse hook that blocks destructive git, database-altering and secret-printing commands before the agent runs them. Covers Claude Code, Antigravity and OpenCode. Use when setting up an agent workspace or a VPS agent.
compatibility: claude, antigravity, opencode
---

# Kore guardrails

Derived from `git-guardrails-claude-code` (Matt Pocock, MIT). Each harness blocks differently, so there are two scripts.

## Blocked (both)

- Git: `push`, `reset --hard`, `clean -f`, `branch -D`, `checkout .`, `restore .`
- Database: `prisma migrate`, `prisma db push|execute`, `db:migrate`, `db:seed`, `DROP TABLE|DATABASE`, `TRUNCATE`
- Secrets: reading a real `.env` (allows `.env.example/.sample/.template`), `printenv`, bare `env`

## Claude Code — `scripts/block-dangerous.sh`

Reads `tool_input.command`, blocks with exit code 2. No `jq` needed. Wire as a `PreToolUse` / `Bash` hook in `.claude/settings.json`:

```json
{ "hooks": { "PreToolUse": [ { "matcher": "Bash",
  "hooks": [ { "type": "command", "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-dangerous.sh\"" } ] } ] } }
```

Verify: `echo '{"tool_input":{"command":"git push"}}' | bash .claude/hooks/block-dangerous.sh` exits 2 with `BLOCKED`.

## Antigravity — `scripts/block-dangerous-agy.py`

Antigravity does NOT use exit codes. It reads `toolCall.args.CommandLine` (and file paths for `view_file`/`read_file`) from stdin JSON and blocks with `{"decision":"deny"}` on stdout. Wire in `~/.gemini/config/hooks.json` with matcher `run_command|view_file|read_file`, alongside any existing (e.g. ai-memory) hooks. Needs `python3`.

Verify: `echo '{"toolCall":{"name":"run_command","args":{"CommandLine":"git push"}}}' | python3 block-dangerous-agy.py` prints a `deny` decision.

## OpenCode

OpenCode guardrails are enforced through its own `permission` config and a plugin, not these scripts. See the workspace `opencode.json`.

A blocked command means the user must run it. Do not look for a workaround.
