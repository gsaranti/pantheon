---
name: metis-build-spec
description: Produce BUILD.md — the project's forward-looking architecture brief.
---

# $metis-build-spec

Produce `.metis/BUILD.md`.

## Preflight

Run this skill's `references/build-spec-preflight.sh` before drafting. It exits non-zero if `.metis/BUILD.md` already exists (surface the error, suggest the user delete the file manually if a fresh rewrite is intended, and stop). Otherwise it reports `DOCS_PRESENT`, `RECONCILE_DONE`, and `WALK_PENDING`.

## Input shape

Determined from the preflight + the trailing prompt:

- **Docs-first ready** — `DOCS_PRESENT=yes`, `RECONCILE_DONE=yes`, `WALK_PENDING=no`. Synthesize from the reconciled corpus.
- **Reconcile or walk pending** — `RECONCILE_DONE=no` or `WALK_PENDING=yes`. Suggest the prerequisite command (`$metis-reconcile` or `$metis-walk-open-items`) and proceed only if the user explicitly insists.
- **No docs** — `DOCS_PRESENT=no`. The trailing prompt is required; if absent, stop and ask. If present, classify as **prompt-seeded** (fresh project) or **existing-codebase** (delta on top of code in the repo) based on what the prompt describes.

## Load

- For docs-first: `.metis/SYNTHESIS.md`, `.metis/INDEX.md`, and the source docs under `docs/` at the cited passages.
- For existing-codebase: code from the source tree, via `metis-code-explorer` subagent dispatches.

## Do not load

- `.metis/CONTRADICTIONS.md`, `.metis/QUESTIONS.md`, `.metis/RESOLVED.md`.

## Read first

This skill's `references/writing-build-spec.md` — read before drafting.

## Write scope

One file: `.metis/BUILD.md`.

## Invocation prompt

Trailing prompt: see this skill's `references/command-prompts.md`.

## Return

One message to the user:

- **Path written** — `.metis/BUILD.md`, with one-line summary of the synthesis-like opening and the risk lead.
- **Open assumptions** — anything the brief committed to that the corpus did not settle, surfaced so the user can audit the bet before implementation begins.
- **Next step** — `$metis-plan-task "<description of what to build first>"`. The first vertical slice in `.metis/BUILD.md` is the natural target.
