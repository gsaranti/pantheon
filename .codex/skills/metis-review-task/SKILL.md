---
name: metis-review-task
description: Dispatch the metis-task-reviewer subagent to judge a diff against the task description and plan. Returns a verdict with per-criterion evidence.
---

# /metis-review-task

Dispatch the `metis-task-reviewer` subagent to review one implementation against the description and plan it was meant to satisfy.

## Arguments

- **Trailing prompt** — optional. Augments the dispatch prompt per the command-prompts convention (e.g., narrowing the diff range, flagging a specific concern).

## Context expected

The parent collects what the reviewer needs from conversation context before dispatching:

- The **description** the work was implemented against — from this session's chat history, or rehydrated from `.metis/CURRENT.md` via `/metis-session-start`.
- The **plan**, if one was produced — same sources.
- The implementer's **scope report** — produced by `/metis-implement-task` at the close of implementation; in chat history or in `.metis/CURRENT.md`.

If any of these are missing, ask the user before dispatching. Reviewing an unstated brief is the silent-drift mirror of implementing one.

## Preflight

Run `scripts/review-task-preflight.sh`. It exits non-zero if the working directory isn't a git repo. On success it reports two fields:

- `BASELINE` — the branch the implementation diverges from. First existing of `main`, `master`, `origin/main`, `origin/master`; empty if none exist (the subagent then reviews only uncommitted changes).
- `DIFF_PRESENT` — `yes` if there are uncommitted changes or commits ahead of `BASELINE`; `no` otherwise.

If `DIFF_PRESENT=no`, surface an "empty diff" finding without dispatching — no implementation work to judge.

## Subagent dispatch

Dispatch `metis-task-reviewer` with a single structured prompt containing:

- The description.
- The plan, if one was produced.
- The implementer's scope report.
- The `BASELINE` from the preflight (the branch the subagent should diff against).
- Any trailing prompt the user passed to this skill, verbatim.

The subagent reads the git diff itself; the parent does not need to embed it.

## Write scope

This command writes nothing.

## Invocation prompt

Trailing prompt: forwarded verbatim to the subagent.

## Return

Relay the subagent's return:

- **Verdict** — `approve`, `approve-with-nits`, or `reject-with-reasons`.
- **Per-criterion results** — pass/fail with evidence, for each criterion the description and plan implied.
- **Scope reduction findings** — whether the implementer's scope report honestly describes what's missing, and any reductions the implementer didn't surface.
- **Code-quality notes** — separate from spec compliance.
- **Next step**:
  - `approve` / `approve-with-nits` — user commits/merges.
  - `reject-with-reasons` — back to `/metis-implement-task` with the reviewer's findings as the trailing prompt.

If the subagent returns an "empty diff" finding instead of a review, pass it through as-is.
