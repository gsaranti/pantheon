---
name: metis-walk-open-items
description: Walk captured open items one at a time, resolving each into the relevant source doc.
---

# $metis-walk-open-items

Walk open items — contradictions and gray areas — one at a time, resolving each into the source doc it points at and appending a minimal pointer to `.metis/RESOLVED.md`.

## Preflight

Run this skill's `references/walk-open-items-preflight.sh` before starting. It exits non-zero if `docs/` is missing or if neither `.metis/CONTRADICTIONS.md` nor `.metis/QUESTIONS.md` exists (surface the error, point the user at `$metis-reconcile`, and stop). Otherwise it reports `OPEN`, `OPEN_CONTRADICTIONS`, `OPEN_QUESTIONS`, `DEFERRED`, `STALE`, and `RESOLVED_PRIOR`.

If `OPEN + DEFERRED + STALE == 0`, report the empty set and suggest `$metis-build-spec`. Otherwise show the counts and present a lettered navigation menu:

```
[A] - Continue from the next open item
[B] - List all items
[C] - Pick by number (type a number or item id)
[Q] - Quit
```

After resolving an out-of-order item, ask whether to continue or pick another using the same lettered format.

## Pacing

After each item: present the proposal in the lettered-menu format from this skill's `references/walking-open-items.md`, then wait for the user's input — pick a letter, type a custom answer, type `defer`, or type `quit`. The user has unbounded thinking time; do not chain items. The narrow auto-land carve-out in this skill's `references/walking-open-items.md` is the exception; the rhythm is one item, one user response.

## Load (per item)

- The one open item being walked — its status header, cited passages, and framing from the active file.
- The source-doc passages it cites. Re-open the source at the cited section; do not work off the capture's paraphrase.

## Do not load

- `.metis/RESOLVED.md`.
- `.metis/BUILD.md`.
- Other open items.

## Read first

This skill's `references/walking-open-items.md` — read before offering options on the first item.

## Write scope

Walks are item-by-item, so prefer Edit for surgical operations: remove one resolved item, update one item's status, append one new item, append one pointer. Avoid Write where Edit suffices — re-emitting unchanged items as Write output is the cost we're avoiding.

- Source docs under `docs/` — the smallest edit per resolution.
- `.metis/CONTRADICTIONS.md` and `.metis/QUESTIONS.md` — Edit to remove resolved items, update status on `deferred` or `stale`, append newly surfaced items when a resolution spawned one.
- `.metis/RESOLVED.md` — append the minimal pointer per resolved item. Create the file if absent (no preflight stub for this one — it earns existence on the first resolution).

Do not write to `.metis/BUILD.md`.

## Invocation prompt

Trailing prompt: see this skill's `references/command-prompts.md`.

## Return

When the user quits the walk or the open set is empty:

- **Resolved this session** — count plus the pointers appended to `.metis/RESOLVED.md`.
- **Remaining** — open, deferred, stale counts split by file.
- **Doc edits** — list of source docs changed, one line per edit.
- **Next step** — `$metis-build-spec` when the open set is empty (or consciously deferred); otherwise a note that the walk can be resumed next session.
