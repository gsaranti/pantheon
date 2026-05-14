---
name: metis-session-start
description: Rehydrate a fresh session from on-disk state.
---

# $metis-session-start

Read the minimum set of files that orients the agent to the project's current state.

## Preconditions

`.metis/` must exist. If it does not, stop and point at `$metis-init`.

Partial state inside `.metis/` (missing or incomplete files) surfaces as an Anomaly in the Return rather than a hard error.

## Load

In this order:

1. **`.metis/CURRENT.md`** — the previous session's handoff. The primary rehydration source.
2. **`.metis/BUILD.md`** — the architecture brief, when it exists. Loaded once at session start so the rest of the session's work can lean on it without re-reading.
3. **`.metis/INDEX.md`** — the concept → source-doc map, when it exists.

## Do not load

- `.metis/SYNTHESIS.md`, `.metis/CONTRADICTIONS.md`, `.metis/QUESTIONS.md`, `.metis/RESOLVED.md` — reconcile artifacts. Loaded on demand by the skills that need them, not at session start.
- `docs/` — source corpus. Loaded on demand by skills that turn on specific passages.

## Write scope

**None.**

## Return

- **What happened last session** — one paragraph from `CURRENT.md` *What happened*. If `CURRENT.md` is missing or empty, say so directly.
- **In flight** — what's being worked on right now, from `CURRENT.md` *Current state*. If nothing is in flight, say so.
- **Open questions** — the list from `CURRENT.md` *Open questions*. Surfaced as items the user may want to address.
- **Where to start** — directly from `CURRENT.md` *Where to start*. Do not rewrite — pass it through.
- **Anomalies** — anything unexpected: missing `CURRENT.md` (suggest `$metis-init`), `CURRENT.md` referencing files that don't exist on disk, `.metis/BUILD.md` mentioned by the handoff but absent. Surface rather than absorb.

## Invocation prompt

Silently accept and ignore any trailing free-text prompt.
