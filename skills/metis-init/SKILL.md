---
name: metis-init
description: Finalize project-specific Metis setup. Thin wrapper around the plugin's init.sh — creates .metis/, populates .metis/config.yaml, splices a delimited block into CLAUDE.md, and writes a .metis/CURRENT.md stub.
disable-model-invocation: true
---

# /metis-init

Run `${CLAUDE_PLUGIN_ROOT}/.metis/scripts/init.sh` and relay its output verbatim. The script handles arguments (`--name=<name>`, `--reinit`), preconditions, interactive prompts, and re-run idempotency; this skill does not intermediate.

## Write scope

None. The script writes.

## Invocation prompt

Silently accept and ignore any trailing free-text prompt.
