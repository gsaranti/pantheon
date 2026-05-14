---
name: metis-implement-task
description: Implement a planned task. Closes with a scope report.
---

# $metis-implement-task

Implement the task described by the plan in context, and close with a scope report.

## Arguments

- **Trailing prompt** — optional. Augments the plan in context per the command-prompts convention. If no plan is in context, the prompt serves as the description and the agent treats it as a single-step brief.

## Context expected

A plan or description present in conversation context. It can come from any of:

- A recent `$metis-plan-task` invocation in this session — structured plan in chat history.
- An informal plan or description discussed with the user in this session before invoking this skill — chat history, however it got there.
- `.metis/CURRENT.md` loaded by `$metis-session-start` — a prior session captured the plan there.
- The trailing prompt to this command, when it's specific enough to serve as the brief.

If none of these are present, ask the user before proceeding. Implementing against an unstated brief is the silent-drift failure mode this skill exists to avoid.

## Load (task-specific)

- The code the task is changing, on demand as implementation proceeds. Confined to surfaces named in the plan's expected file changes — widening goes in the scope report.
- Source-doc passages the plan cites or the description points at, at the named paths.

## Do not load

- `.metis/CONTRADICTIONS.md`, `.metis/QUESTIONS.md`, `.metis/RESOLVED.md`.
- Other session state beyond the plan and what the plan points at.

## Read first

This skill's `references/honest-scope-reporting.md` — read before composing the closing scope report.

## Write scope

- **Code and test files.** Confined to surfaces named in the plan's expected file changes. Widening — touching files the plan did not name — goes in the scope report.

### Do not write to

- Any file under `.metis/`. The plan, the build spec, session state — none of these are implementation-time concerns. `$metis-session-end` is what captures implementation state in `.metis/CURRENT.md` if the session ends before review.
- `.claude/`.

## Invocation prompt

Trailing prompt: see this skill's `references/command-prompts.md`.

## Knowing when to stop

If the verification command fails repeatedly, prefer surfacing the problem to grinding on it. Three signals that the right move is to stop and report rather than keep fixing:

- **Scope creep.** A fix you'd make would touch files outside the plan's expected file changes — even if it would make verification pass. The plan named a surface; widening it unilaterally to chase a failure is exactly the silent-drift mode this skill exists to avoid.
- **No progress.** Two consecutive fix attempts produce errors with the same root cause — different surface symptom, same underlying failure. The agent is going in circles, not learning.
- **Collateral risk.** The fix you're considering looks plausible for the immediate failure but risks breaking behavior the plan does not touch — an unrelated test, an integration the plan did not anticipate.

When any of these hit, stop. Do not commit further fixes. Close with the verification output as-is, a one-line description of what was tried, and a Finding flagging the likely failure mode (description-vs-implementation gap, stale test fixture, dependency the plan didn't anticipate, two unrelated outcomes bundled into one task, etc.). A verification failure that takes the implementation outside its planned shape is a signal that the plan or description was wrong — not a problem the implementer should solve by widening on the fly.

## Closing the implementation

Before returning:

1. Run the plan's verification command (or, if no plan, an agent-derived command that proves the description's outcome). Paste the actual output into the return message — not a claim of what it said. If verification is stuck per the *Knowing when to stop* signals above, close anyway with the failure as-is.
2. Compose a scope report per this skill's `references/honest-scope-reporting.md` — four categories (Skipped / Deferred / Stubbed / Handled differently), no defense. An empty report is fine when the work met its criteria cleanly; say so in one line.

The scope report and verification output live in the return message in chat. `$metis-session-end` captures them in `.metis/CURRENT.md` if the session ends before review.

## Return

- **Files changed** — the actual code and test paths touched, one line each.
- **Verification result** — the command run, its exit, and the relevant lines of output.
- **Scope report** — the four-category block (or "empty — work met its criteria cleanly" if nothing was reduced).
- **Findings** — upstream flags: description gaps, scope conflicts, architectural questions the implementation surfaced.
- **Next step** — `$metis-review-task` to dispatch the reviewer subagent against the diff + scope report.
