#!/usr/bin/env python3
"""Antigravity CLI PreToolUse guardrail (matcher: run_command).

Reads the hook payload as JSON on stdin, inspects the shell command in
toolCall.args.CommandLine, and blocks destructive git, database-altering and
secret-printing commands by printing {"decision":"deny",...} to stdout.
Safe commands produce no output, so Antigravity's normal permission flow
continues. Fails closed: an unreadable run_command payload is denied.
"""
import json
import re
import sys

PATTERNS = [
    r"git(\s+-[^\s]+(\s+[^-\s][^\s]*)?)*\s+push",
    r"git\s+reset\s+--hard",
    r"git\s+clean\s+-[a-z]*f",
    r"git\s+branch\s+-D",
    r"git\s+(checkout|restore)\s+\.",
    r"prisma\s+migrate",
    r"prisma\s+db\s+(push|execute)",
    r"db:(migrate|seed)",
    r"(DROP|TRUNCATE)\s+(TABLE|DATABASE|SCHEMA)",
    r"TRUNCATE\b",
    r"(cat|type|more|less|head|tail|Get-Content|gc)\s+[^|;&\"]*\.env",
    r"printenv",
    r"(^|[;&|\"\s])env\s*(\||;|&|\"|$)",
]


def deny(reason):
    print(json.dumps({"decision": "deny", "reason": reason}))
    sys.exit(0)


def main():
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except Exception:
        # Not parseable: do not interfere with non-run_command events.
        return
    tool = (payload.get("toolCall") or {}).get("name", "")
    args = (payload.get("toolCall") or {}).get("args") or {}

    # File-read tools: block reading a real .env (allow .env.example/.sample/.template).
    if tool in ("view_file", "read_file", "read_many_files", "cat_file"):
        for key in ("AbsolutePath", "Path", "path", "file", "TargetFile"):
            val = args.get(key)
            if isinstance(val, str):
                cleaned = re.sub(r"\.env\.(example|sample|template)", "", val)
                if re.search(r"\.env(\.|$|[^a-zA-Z])", cleaned):
                    deny("kore-guardrails blocked reading an environment file. "
                         "The user must handle secrets themselves.")
        return

    if tool and tool != "run_command":
        return
    cmd = args.get("CommandLine")
    if not isinstance(cmd, str):
        if tool == "run_command":
            deny("kore-guardrails: could not read CommandLine from a run_command payload")
        return
    probe = re.sub(r"\.env\.(example|sample|template)", "", cmd)
    for p in PATTERNS:
        if re.search(p, probe):
            deny("kore-guardrails blocked a destructive command (pattern: %s). "
                 "The user must run this themselves." % p)
    # safe: emit nothing, let the normal flow decide.


if __name__ == "__main__":
    main()
