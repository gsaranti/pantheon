# Planning a task

A plan is the bridge from a description to the implementer. The job of this skill is to take a free-text task description plus the project's architectural context (`.metis/BUILD.md`) and render it into a short, sequenced plan an implementer can execute without re-deriving the work. The plan does not contain code; it names the changes and the order they go in. The plan lives in chat — no file is written.

Two failure modes pull against each other. Over-planning prescribes every keystroke and pretends the description didn't already say what to do; the implementer reads a redundant summary before doing the work anyway. Under-planning hands over an outline — "add the handler, wire the verifier, test it" — and calls sequencing left to the reader a plan; the implementer ends up decomposing mid-implementation.

## Read first

- The task description, as the user typed it. Treat it as the brief; if it is vague, ask before guessing.
- `.metis/BUILD.md` and `.metis/INDEX.md` — expected to be loaded by `/metis-session-start`. The first vertical slice section and the data model in `BUILD.md` are the most-often relevant sections; the risk lead is what the plan should not silently work against. `INDEX.md` is the lookup from concept to source-doc path when the description names a topic the docs cover.
- Source-doc passages the description points at, when the description names specific concepts (e.g. "implement signature verification" → `docs/security.md §Webhook verification`).

## Artifact shape

The plan, presented in chat as structured markdown, with three top-level sections:

- **Ordered steps** — the numbered sequence the implementer walks. Each step names the change in prose, the concrete files or modules it touches (a speculative touch list is noise; list only files the step can name confidently), and the test approach for that step (see *Test approach without forced TDD* below).
- **Verification command** — one command (or a minimum set) that shows the work is done.
- **Assumptions and flags** — what the plan had to guess (named), and what it could not settle and is returning upstream.

Files and test approach live inside the per-step content rather than as separate top-level sections — a cross-step touch list is just the cumulative content of the steps, and a separate test-approach section would either be redundant with the step or hide the per-step choice. Sections beyond these three belong in conversation around the plan, or the plan was never a plan.

## Ordered steps, not a checklist

Sequencing is the point. A set of bullets that could be executed in any order is a decomposition, not a plan — the implementer still has to work out which bit unblocks which. Number the steps and make the dependency between them explicit when the order alone does not show it.

Step granularity is a judgment call. A step that needs more than ~100 tokens of description is usually two steps; a step described in fewer than ~10 tokens is usually three steps hidden in a checkbox. The working test: can the implementer execute this step, verify it, and move on without reading the next step first? If no, it is not one step.

## Test approach without forced TDD

Name the approach that fits the change. Tests-first earns its cost when the contract is sharp and known in advance — a pure function, a new endpoint with specified inputs and outputs, a migration's post-state. Tests-after is honest when the shape is itself the unknown — a refactor in progress, a spike, a UI pass where the assertion only comes from seeing the thing run. Some steps modify no behavior worth testing — a rename, a config change, a dependency bump — and the plan says so rather than manufacturing a test to preserve ritual.

Pick the register per step, not per plan. A plan with one contract-shaped step and one refactor-shaped step is allowed to mix.

## The verification command

Name a specific command the plan promises will show the implementation works end-to-end — `pytest tests/billing/test_webhook.py::test_signature_failure`, not "run the tests." Prefer the repo's native entry point (`make test`, `npm test -- <target>`, whatever the project already uses) over an invented shell recipe. The specificity is what makes the plan checkable: the implementer runs the command, the reviewer reads its output, neither of them has to rediscover what "the tests" meant.

If no single command can prove the work, name the minimum set and state what each one covers. Two commands with clean purposes beats one vague one. A plan that cannot name a verification command at all has not committed to what "done" looks like.

## Assumptions vs. flagged ambiguities

An **assumption** is a guess the plan needed to make and can name. Because it is named, the implementer and reviewer can check whether it held; the plan is still honest. *"Assumes the existing `WebhookError` type carries the right fields for the new code path — fall back to a dedicated type if not"* is an assumption worth keeping moving on.

A **flag** is a gap the plan could not settle without guessing in a way that would not be checkable. Local flags — a field type, a specific error code — go in the plan's flags section and the implementer is told to defer them upward. Structural flags — a description that turns on behavior the source docs do not pin down, or a description that bundles two unrelated outcomes — do not belong in a flags section. They belong upstream — the finding is that the description itself is underspecified, not that the plan needs more words. Surface them as a request for clarification before drafting.

## The task may already be done

Before sequencing the plan, a light check against what the description implies is worth the cost. Infer the rough surface the work would touch — files, modules, endpoints — and glance for evidence the commitments are already in the code. If they are, the right return is not a plan — it is a finding naming which files already exist and which parts of the description are visibly met. The user decides from the finding what to do next.

The bar is *is there evidence the work is substantially done*, not *is every implication verified*. A full verification would re-read files the plan should only glance at; it belongs downstream of the plan, not inside it. When evidence is ambiguous — some surface present, some parts of the description partially evident — produce the plan but flag the overlap in its assumptions section so the user can weigh the overlap against proceeding. A plan that proceeds as if the code were absent when it is obviously present is the same kind of silent drift this skill warns against in the other direction.

## Pushing back on the description

This is the one upstream-facing register the plan carries. When a description's outcome cannot be made testable without an extra call, when two honest plans could be written depending on a scope detail the description did not fix, when the description bundles two unrelated outcomes, or when making the plan honest would require commitments outside the description's scope, the plan's job is to surface the gap upstream — not to widen itself until the ambiguity is hidden inside the steps. A plan that silently resolves a description ambiguity is where silent drift starts.

## Code exploration when the surface is unfamiliar

Inline `Read` / `Glob` / `Grep` is the default for small lookups. A `metis-code-explorer` dispatch earns its cost only when the surface is unfamiliar enough that planning would be guessing — an entry point the description names but does not bound, a refactor target whose call sites span modules, a layer the description touches whose shape neither the description nor `.metis/BUILD.md` describes.

The report's file:line refs land in the plan's *Expected file changes* section. When a surprise comes back — a side effect the description's framing missed, an existing handler that already does part of the work — surface it as an upstream flag against the description rather than absorbing it into the plan. A description whose framing is wrong should be amended; planning around the wrongness is the silent-drift register.

## Research, when the corpus does not cover it

When a plan step would have to commit to a technical choice the description and `.metis/BUILD.md` do not cover, dispatch `metis-domain-researcher` and plan against the result. The findings return inline; the recommendation flows into the plan step it informs.

## Sizing as feedback

Short by default — ~500–1,500 tokens for a normal task plan. The diagnostic is whether each section still earns its place, not the absolute count. A plan that has outgrown its description is usually two tasks wearing one plan (push it back upstream), or a plan that has started narrating intent between steps rather than sequencing them (trim the prose, keep the steps). A plan under ~150 tokens is almost always missing the verification command or the flags section.
