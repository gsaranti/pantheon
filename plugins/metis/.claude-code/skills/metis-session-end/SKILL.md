---
name: metis-session-end
description: Update .metis/CURRENT.md with the session handoff.
disable-model-invocation: true
---

# /metis-session-end

Close out the session: rewrite `.metis/CURRENT.md`.

## Preconditions

`.metis/` must exist. If it does not, stop and point at `/metis-init`.

## Load

- The current `.metis/CURRENT.md`.
- The session's in-flight state from conversation context — what just happened, what was decided, what is queued, any plan or scope report mid-flow.

## Do not load

- Other `.metis/` artifacts (`BUILD.md`, `SYNTHESIS.md`, `INDEX.md`, `CONTRADICTIONS.md`, `QUESTIONS.md`, `RESOLVED.md`). The handoff is about session state, not project state.
- `docs/`.

## Read first

`references/session-handoff.md` — read before writing the handoff.

## Write scope

- **`.metis/CURRENT.md`** — full rewrite. The handoff is the cumulative summary of session state, not an append log.

### Do not write to

- Other `.metis/` files.
- `docs/`.
- `.claude/`.

## Invocation prompt

Trailing prompt: see `${CLAUDE_PLUGIN_ROOT}/references/command-prompts.md`.

## Return

- **Handoff summary** — the four blocks of the new `CURRENT.md`, rendered inline.
- **Pending decisions** — any architectural choice made this session that should be remembered next time but wasn't captured (in `.metis/BUILD.md`, in code, or in a commit message). Surfaced as a flag for the user to decide whether to revise `BUILD.md`.
- **Next step** — typically the session ends here.
