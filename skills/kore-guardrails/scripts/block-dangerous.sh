#!/bin/bash
# Blocks destructive git, DB-altering and secret-printing commands. Needs no jq.
INPUT=$(cat | sed -E 's/\.env\.(example|sample|template)//g')
PATTERNS=(
  'git([[:space:]]+-[^[:space:]]+([[:space:]]+[^-[:space:]][^[:space:]]*)?)*[[:space:]]+push'
  'git[[:space:]]+reset[[:space:]]+--hard'
  'git[[:space:]]+clean[[:space:]]+-[a-z]*f'
  'git[[:space:]]+branch[[:space:]]+-D'
  'git[[:space:]]+(checkout|restore)[[:space:]]+\.'
  'prisma[[:space:]]+migrate'
  'prisma[[:space:]]+db[[:space:]]+(push|execute)'
  'db:(migrate|seed)'
  '[Dd][Rr][Oo][Pp][[:space:]]+(TABLE|DATABASE|SCHEMA)'
  '[Tt][Rr][Uu][Nn][Cc][Aa][Tt][Ee]'
  '(cat|type|more|less|head|tail|Get-Content|gc)[[:space:]]+[^|;&"]*\.env'
  'printenv'
  '(^|[;&|"[:space:]])env[[:space:]]*(\||;|&|"|$)'
)
for p in "${PATTERNS[@]}"; do
  if printf '%s' "$INPUT" | grep -qE -- "$p"; then
    echo "BLOCKED by kore-guardrails (pattern: $p). The user must run this command themselves." >&2
    exit 2
  fi
done
exit 0
