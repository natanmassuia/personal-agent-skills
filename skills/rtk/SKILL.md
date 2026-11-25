---
name: rtk
description: Route shell commands through rtk, the output compressor that strips noise from command results before they reach the context window. Use whenever a command is about to produce verbose output (git, ls, grep/rg, find, tests, linters, compilers, docker, kubectl, cloud CLIs, curl, logs, JSON), when the user says "rtk", "compress the output", "save tokens", "bypass", or "recall", or when a filtered result looks truncated and needs recovery.
argument-hint: "<command-to-run> [--bypass|--gain]"
---

# RTK — command output compression

`rtk` is a CLI proxy installed on this machine (`rtk.exe` on PATH, via WinGet). It runs the
real command and prints a condensed version: every signal kept, boilerplate dropped.

Command Code has no hook that can rewrite a tool call, so **route the command yourself**:
prefix it with `rtk`.

## Core rule

Treat filtered output as the complete result. Do not re-run a command just because the
output looks short, and batch related commands into one call instead of spending turns.

## Command map

| Instead of | Run |
| --- | --- |
| `ls`, `tree` | `rtk ls`, `rtk tree` |
| `cat <file>` (large/noisy) | `rtk read <file>` |
| `find ...` | `rtk find ...` |
| `grep -rn ...`, `rg ...` | `rtk grep ...`, `rtk rg ...` |
| `git status/diff/log` | `rtk git status` / `rtk git diff` / `rtk git log` |
| `gh ...`, `glab ...` | `rtk gh ...`, `rtk glab ...` |
| `npm`, `pnpm`, `npx`, `bun` | `rtk npm`, `rtk pnpm`, `rtk npx`, `rtk bun` |
| `tsc`, `eslint`, `prettier` | `rtk tsc`, `rtk lint`, `rtk prettier` |
| `jest`, `vitest`, `pytest`, `playwright`, `ctest`, `rspec`, `phpunit` | `rtk jest`, `rtk vitest`, `rtk pytest`, `rtk playwright`, `rtk ctest`, `rtk rspec`, `rtk phpunit` |
| `cargo`, `go`, `dotnet`, `mvn`, `gradlew`, `rubocop`, `ruff`, `mypy`, `pip`, `uv` | same namespaced form |
| `docker`, `kubectl`, `oc`, `aws`, `psql` | same namespaced form |
| `curl`, `wget`, `jq`/JSON dumps | `rtk curl`, `rtk wget`, `rtk json` |
| any command, errors only | `rtk err <cmd>`, `rtk test <cmd>`, `rtk summary <cmd>`, `rtk smart <cmd>` |
| dependency inventory | `rtk deps` |
| env dump | `rtk env` |

`rtk diff` gives an ultra-condensed diff, `rtk log` filters and deduplicates logs.

## Recovery and fallback

- Truncated or elided output: the filter prints a content hash — `rtk recall <hash>` returns
  the elided part.
- Unusable output (empty when output was clearly expected, contradicts the exit code, or
  garbled): re-run once as `rtk bypass <cmd>` to get raw output.
- Need to know what rtk would do without running it: `rtk hook check "<cmd>"`.
- Savings report: `rtk gain`.

## Don't bother

Skip rtk for commands whose output is already tiny or structured (short `git rev-parse`,
`echo`, a two-line `wc -l`) — the wrapper costs a process and saves nothing. Never route
interactive or stateful commands (`vim`, `ssh`, `npm init`, watch mode) through it.
