---
name: metis-plan-task
description: Produce an implementation plan for a free-text task description. Plan stays in chat.
---

# $metis-plan-task

Produce one implementation plan for a free-text task description. The plan stays in chat; nothing is written to disk.

## Arguments

- **Trailing description** — required. A short free-text description of the task to plan. Example: `$metis-plan-task "implement Stripe webhook signature verification"`.

## Context expected from session-start

`.metis/BUILD.md` and `.metis/INDEX.md` (when it exists) are expected to be in context already (loaded by `$metis-session-start`). `BUILD.md` is the architecture; `INDEX.md` is the concept → source-doc map, useful for finding the passages a description points at.

If either is missing — the session began without a session-start — read them lazily as the plan turns on them. Subsequent turns are cache hits.

## Load (task-specific)

- The source-doc passages or code seams the description points at. Use `.metis/INDEX.md` to look up source-doc paths for concepts the description names, `.metis/BUILD.md` to identify likely architecture sections, then read source docs at the named paths.
- `metis-code-explorer` subagent dispatches when the surface is unfamiliar enough that planning would be guessing.
- `metis-domain-researcher` subagent when a plan step would commit to a technical choice the corpus does not cover.

## Do not load

- `.metis/CONTRADICTIONS.md`, `.metis/QUESTIONS.md`, `.metis/RESOLVED.md` — these belong to the reconcile/walk flow, not to planning.
- Other session state beyond `BUILD.md` and what the description points at.

## Read first

This skill's `references/planning-a-task.md` — read before drafting.

## Write scope

None. The plan is presented in chat as structured markdown. If the session ends mid-plan or before implementation, `$metis-session-end` captures the relevant plan content in `.metis/CURRENT.md` so the next session can resume.

## Invocation prompt

The free-text description after the command is the planning prompt — required, not optional. An empty description means stop and ask the user what to plan rather than guessing.

## Return

The plan, in chat, with the shape from this skill's `references/planning-a-task.md`.

After the plan: one line on the next step (`$metis-implement-task` to execute), and a tip: *"For Claude Code's native plan-mode review UI, run this in plan mode (Shift+Tab) before invoking."*

If the task appears already substantially done (per the "already done" check in this skill's `references/planning-a-task.md`), return the evidence finding instead of a plan.
