---
name: metis-reconcile
description: Read the docs corpus and produce SYNTHESIS.md, INDEX.md, CONTRADICTIONS.md, and QUESTIONS.md in .metis/.
disable-model-invocation: true
---

# /metis-reconcile

Read everything under `docs/`. Produce four reconcile artifacts: `.metis/SYNTHESIS.md`, `.metis/INDEX.md`, `.metis/CONTRADICTIONS.md`, `.metis/QUESTIONS.md`.

## Preflight

Run `references/reconcile-preflight.sh` before reading. It exits non-zero if `docs/` is missing (surface the error and stop). Otherwise it reports `STATUS` (`fresh` / `rereconcile`), `SIZE_CLASS` (`small` / `medium` / `large`), and counts for the corpus and any prior items.

On `SIZE_CLASS=large`, apply the slicing guidance in `references/reconciling-docs.md`.

## Load

- The source docs under `docs/`.
- On `rereconcile`, the prior `.metis/CONTRADICTIONS.md` and `.metis/QUESTIONS.md`. Re-reconcile preserves prior items and re-checks them against the current corpus (per `references/reconciling-docs.md`) rather than starting over.

## Do not load

- `.metis/RESOLVED.md`.
- `.metis/BUILD.md`.

## Read first

`references/reconciling-docs.md` — read before drafting any of the output artifacts.

## Write scope

Four files in `.metis/`. The preflight pre-creates stubs if absent, so all four exist before write time and Edit can target them on the first run.

- `.metis/SYNTHESIS.md` — full Write each run. The synthesis is regenerated from the current corpus, not patched.
- `.metis/INDEX.md` — Write from scratch on `STATUS=fresh`. On `STATUS=rereconcile`, prefer Edit: add, update, or remove individual entries surgically and leave unchanged entries in place.
- `.metis/CONTRADICTIONS.md` — same Edit-preferred discipline on rereconcile. Preserve items marked `stale`. Re-emitting unchanged items as Write output is the cost we're avoiding.
- `.metis/QUESTIONS.md` — same treatment as `CONTRADICTIONS.md`.

Do not write to `.metis/RESOLVED.md`, any source doc under `docs/`, or `.metis/BUILD.md`.

## Invocation prompt

Trailing prompt: see `${CLAUDE_PLUGIN_ROOT}/references/command-prompts.md`.

## Return

One message to the user:

- **Files written** — four paths with item counts per `CONTRADICTIONS.md` / `QUESTIONS.md` (open / deferred / stale).
- **Coverage** — which docs were read in full vs. sliced, and any passages deliberately deferred to a later pass. On `SIZE_CLASS=large`, include the completeness caveat here.
- **Next step** — `/metis-walk-open-items` when there are open or stale items; `/metis-build-spec` when the open set is empty.
