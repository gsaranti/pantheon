# Reconciling docs

A reconcile pass produces a set of files that together make a docs corpus reviewable: `SYNTHESIS.md`, `INDEX.md`, `CONTRADICTIONS.md`, `QUESTIONS.md`. The job of this skill is to read the corpus thoroughly enough that contradictions and gaps surface, to capture each finding as a well-framed item — neutral, citable, ready for a later walk, without taking a side — and to leave behind an own-words summary of what is being built. Resolution is a separate artifact and a separate skill; the architecture brief in `BUILD.md` is build-spec's job, downstream of this one.

Two failure modes pull against each other: surfacing too little, so contradictions and silences live on as silent assumptions that compound once code starts; and surfacing too much, so the walk drowns in items that were never really issues — a term used two ways inside a paragraph, a wording drift with no implementation consequence.

## Artifact shape

A reconcile pass produces four files in `.metis/`:

- **`SYNTHESIS.md`** — own-words summary of what is being built. Roughly 500–1,000 tokens — a short orientation read.
- **`INDEX.md`** — concepts → file + section map.
- **`CONTRADICTIONS.md`** — open and deferred items only. One `##` heading per item.
- **`QUESTIONS.md`** — open and deferred items only. One `##` heading per item.

An open item has a status header and the substance a later reader needs in order to walk it without re-reading the corpus:

```markdown
## C2: Session persistence vs. token lifetime
Status: open
Added: 2026-04-18

docs/auth.md §Sessions: "Sessions persist across browser restarts."
docs/security.md §Tokens: "All access tokens are short-lived (≤15 min)."

These specify the same surface differently: one commits to persistence
across restarts, the other to short-lived tokens. A resolution has to
name how both hold together, or which gives way.
```

Item statuses at capture: `open` (default) or `deferred` (captured but explicitly set aside for later). `stale` and `resolved` are lifecycle states owned by the walk.

## Reading the corpus well

Detection is a property of the read, not a step taken after it. A sequential skim — one doc at a time, finish-before-moving-on — misses the contradictions and drifts that only show up when two docs' views of the same concept sit side by side. The reconcile read is closer to a careful first pass over a long specification: cross-referential, multi-pass, willing to jump between docs as a concept surfaces in each of them.

Two passes is the minimum. The first builds the concept map — write `INDEX.md` as you go, not after — because an index under construction is the forcing function for terminology drift: a concept ends up under two names, or a name points at two concepts, precisely when a drift exists. The second pass cross-references: with the map in hand, visit each concept's entries and read the surrounding passages together. Disagreements show themselves here. A pass ends when the next passage would not change `INDEX.md`, `SYNTHESIS.md`, or the open-item set — not when every doc has been visited.

Pass boundaries are natural context resets. The second pass does not need the full reading trace of the first — it needs `INDEX.md`, `SYNTHESIS.md`, and the passages the map points at. Keeping the between-passes state to what the second pass actually needs is what makes cross-referential reading affordable across a corpus of any size.

`SYNTHESIS.md` is the forcing function for gap detection. A sentence of the summary that cannot be written without guessing is hiding a question — write the honest sentence, then capture the gap as a `Q` entry and come back. `BUILD.md` later draws on this synthesis when the architecture brief is written; reconcile leaves the synthesis behind so the next session can orient without re-reading the corpus.

If the corpus is too dense to take in full, read a smaller coherent slice (one subsystem, one flow) cross-referentially and reconcile that slice before moving on. A skim across everything catches less than a thorough read of half.

## Contradiction vs. gray area

A **contradiction** is two specified things disagreeing. Both passages exist; a resolution has to take a side or reshape the surface so both hold. Goes in `CONTRADICTIONS.md`.

A **gray area** is one thing underspecified — a silence, an implicit assumption, a term used loosely enough to mean two things. A resolution has to *specify* rather than choose. Goes in `QUESTIONS.md`.

The test when an item could read either way: can two careful readers land on different concrete answers, each pointing at something the docs say? If yes, contradiction. If both would have to invent, gray area.

## Detection judgment

Patterns that earn an item:

- A term, or a field name, carrying different semantics in different places — or drifting within a single doc.
- Constraints stated once and never reconciled with a contradicting constraint elsewhere.
- A newer doc silently superseding an older one — the older constraint still reads as live and downstream work may still be citing it.
- Implicit assumptions — a doc building on an external service, an auth model, or a tenancy shape no doc names.
- Silences where a reader would have to guess — a flow that stops short of naming the failure mode, a data model without a specified cardinality.

An item that would not change any downstream artifact is noise. A term used loosely but consistently, a passage the codebase already answers unambiguously, a wording choice with no implementation consequence — none of these earn a walk. Attention is the scarce resource of reconciliation; the capture bar is "would a different resolution produce different downstream work?"

## Framing without resolving

Capture-time framing is not the place to propose the answer. A contradiction entry that pre-takes a side, or a question entry phrased as a leading suggestion, biases the later walk; once a decision is appended off a biased frame, the framing is baked in.

For contradictions: quote both sides with their paths (`docs/auth.md §Sessions`), then state the disagreement in one neutral sentence. For questions: quote the passage that points at the topic, then articulate what the docs leave open. "The flow does not specify what happens on signature-verification failure" is a question framing; "should we 400 or 401?" is an answer sneaking in.

## Batch-level check

Glance at the output set as a whole before handing off. Zero items is usually a miss, not a clean bill — most multi-author doc sets carry drifts and silences. Fifty is often one or two underlying disagreements spawning surface items; merge where the same root question has been surfaced twice in different words, and let the merged item carry both citations.
