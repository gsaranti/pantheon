# Writing the build spec

`.metis/BUILD.md` is a short, forward-looking architecture and build plan — roughly 1,500–4,500 tokens — written in the agent's own words from the reconciled corpus. The first vertical slice is specified in it, and the rest of the build leans on it. The job of this skill is to render one `.metis/BUILD.md` that condenses the corpus without restating it, and that commits to the architectural risks it is taking on.

Two failure modes pull against each other. A brief that transcribes the docs — paraphrased section by section, no synthesis across them — adds no judgment a fresh reader would not get more cheaply from `docs/` itself. A brief that skips the load-bearing calls — no named risks, no first slice, no shape for the data model — is too thin to steer the first implementation work and will be rewritten on first contact.

## Read first

- `.metis/SYNTHESIS.md` and `.metis/INDEX.md` if they exist — orientation artifacts over the reconciled corpus. Used to choose which source docs to re-open, not as the brief's content.
- The source docs under `docs/` at the passages the brief will synthesize from. Open them at the cited sections rather than working off the orientation's paraphrase.

For an existing-codebase project, the relevant code is loaded via `metis-code-explorer` subagent dispatches — see *Code exploration in existing-codebase mode* below — not by reading the source tree directly.

## Synthesis-like opening

`.metis/BUILD.md` opens with a concise synthesis-like entry — roughly 100–250 tokens — that says what is being built before the architecture details. This draws on `.metis/SYNTHESIS.md` but reframes for the architecture context: where `SYNTHESIS.md` is the standalone orientation read over the reconciled corpus, the build-spec opening is the architecture's elevator pitch — what the system is, who it serves, what shape it takes. Kept short on purpose; the substance of the architecture starts in the risk lead.

For a prompt-seeded project (no `docs/` corpus), the opening is drawn from the trailing prompt and the agent's own framing, not from a synthesis file.

## Risk-first framing

Name the riskiest architectural decision after the synthesis opening, before committing to the details that depend on it. A brief that jumps straight from synthesis to data model has already bet on the decision underneath them; the reader cannot tell what the bet is or whether it held. Lead with the one call the rest of the architecture is most sensitive to — the system boundary that decides how much state lives server-side, the integration that forces a particular async shape, the identity model the downstream schema assumes — and state it committally.

Risk comes from the corpus, not from invention. The right risk to lead on is the largest resolved question, the most load-bearing constraint, or the thing downstream implementation will have to work around if the call turns out wrong. If no risk can be named, either the brief is premature or the corpus is still missing its sharp edges — surface that in the build spec rather than padding.

## Own words, not transcription

Restate the corpus's commitments in the brief's own synthesis. If a paragraph of `.metis/BUILD.md` could be replaced by a quote from `docs/`, it should be a link, not a copy — the value the brief adds is what the docs mean when held together, not what they said section-by-section. The test: with the source docs open next to the brief, can a reader tell what judgment the brief is making across them? If each paragraph just mirrors one doc section, no judgment is being made.

Where the corpus doesn't settle a call the brief has to make, name the assumption rather than writing through the gap. A reader should be able to tell what the brief inherited from the docs and what it decided on its own.

## Excerpt vs. summarize

Summarize by default. Quote verbatim only when the exact words are load-bearing — a specific contractual constraint, a named exit condition, a clause the implementer must treat as literal. Every quote carries its source path inline (`` `docs/auth.md §Sessions` ``) so a reader can always drop back into the original. A paraphrase of a contractual commitment is a silent weakening; if the exact words matter downstream, quote them.

## Forward-looking, not backward

`.metis/BUILD.md` states what is being built. It does not describe the existing system. For an existing-codebase project, the brief describes the delta — what this build adds, changes, or replaces — and treats existing surfaces as context from the corpus, not as content to tour. System-state descriptions belong in reconcile artifacts under `.metis/`, not in the build spec.

## What the brief covers

The substantive territory: data model, module boundaries, integrations, testing approach, and the first vertical slice. These are topics to cover when the corpus speaks to them, not a mandated table of contents. Order follows the risk lens — lead with the area the most load-bearing decision sits in, then walk outward to what depends on it. A fixed section order that buries the architectural bet under standard headings fights the risk-first property.

If the corpus covers an area and the brief is silent on it, either include it or say why it is out of scope — silent omission lets drift start before the first task does.

## The first vertical slice

A named section in `.metis/BUILD.md`. This is what the first implementation session builds: the thinnest end-to-end pass through the system that actually runs — one route, one screen, one database write, one passing test, all in one deployable shape. The slice is specified concretely, not categorically: the specific endpoint, the specific entity written, the specific check that proves it end-to-end. A categorical slice ("a read path and a write path") reads like an architecture sketch; a concrete slice reads like a task worth picking up.

The slice earns its own section because it is the architecture's first real test. Where it can, the slice exercises the risk the brief led with — the first runnable pass then doubles as the first check on the architecture's load-bearing bet. If it cannot be named, the architecture has not committed enough to be built against yet.

## Code exploration in existing-codebase mode

When the brief is a delta on top of an existing codebase, dispatch the `metis-code-explorer` subagent eagerly — once per architectural seam the brief is about to commit on (auth shape, data model, integration surface, deployment topology). The report's file:line refs land in the `.metis/BUILD.md` section that turns on the seam — e.g., *"the existing dedup layer at `src/billing/idempotency.py:42-71` keys on event-type; this brief commits to extending it to event-id."*

A `metis-code-explorer` subagent dispatch and a `metis-domain-researcher` subagent dispatch can both apply to one seam — what the existing code does is one question, what the right shape of the new commitment is may be a separate one. Keep them as two dispatches.

## Research, when the corpus does not cover it

When `.metis/BUILD.md` would commit to a technical choice the corpus does not specify — a library, an algorithm class, a system pattern — dispatch the `metis-domain-researcher` subagent. The findings return inline; the recommendation flows into the `.metis/BUILD.md` section that turns on the choice. No separate cite — the substance lives in the brief itself.

## Sizing as feedback

The ~1,500–4,500-token band fits most projects, but it is guidance, not a ceiling or a floor. A simple build honestly lands under that range; a very large one honestly lands over it. Padding a thin draft to hit the range, or cutting a necessary one, produces a worse brief, not a better-shaped one.

The band earns its keep as a diagnostic. If a draft runs long without the scope to justify it, transcription is usually doing work synthesis should be doing — trimming excerpts and pushing detail back into the source docs recovers the range. If a draft runs short on a non-trivial project, the synthesis-opening, risk lead, or first slice has usually been skipped, leaving the reader unable to tell what has been committed to.
