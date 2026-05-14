# Walking open items

An open item is a captured entry in `.metis/CONTRADICTIONS.md` or `.metis/QUESTIONS.md` — a contradiction or gray area surfaced during reconcile and waiting for a position. The job of this skill is to walk one open item to resolution: judging whether the corpus implies an answer, offering 1–2 genuine alternatives, or calling for the user's input; updating the relevant source doc with the chosen answer; and moving the item's lifecycle state so the on-disk files are the next session's resume point.

Two failure modes pull against each other: resolving too eagerly, so the agent picks a side the docs do not actually commit to; and punting every item back to the user with no real thinking, so the walk reverts to the user explaining every call from scratch.

## Read first

- The one open item being walked, and the source-doc passages it cites. Re-open the source at the cited section so the walk is not working off a paraphrase that has since drifted.

## Reading the item before proposing anything

An open item arrives pre-framed by the reconcile pass: quoted passages, a neutral sentence naming the disagreement or gap. Start from the captured framing, but verify the cited passages still say what the item claims. When the quoted text has been rewritten, renamed, or dropped since capture, the item is **stale** — the walk cannot honestly resolve a framing the docs no longer make. Mark the status, note what changed, and leave re-capture to the next reconcile.

## Alternatives, recommendation, or ask

For each open item, pick one of three registers. The pick is the core judgment this skill carries.

- **Two genuine alternatives.** The corpus supports more than one honest reading, each defensible from the cited passages. Surface both with the trade-offs they imply and let the user choose. A genuine alternative is one a careful reader could pick without being pushed; if the second option is weaker on every axis and only exists to make the first look chosen, drop it. A user who accepts the "recommendation" against a straw man has not really chosen.
- **One recommendation.** The corpus implies a single answer the user is very likely to confirm. Surface that read with its reasoning and let the user redirect. A recommendation is honest when inventing a second option would require reaching outside what the docs actually say.
- **Ask.** The corpus genuinely does not imply an answer. Name the gap and ask rather than fabricating options. An invented alternative dressed as a choice is worse than an honest "I don't have a good read here."

The test for which register fits: how much does each candidate answer lean on what the docs say vs. on invention? Heavily on docs → recommendation. Evenly between two doc-supported reads → alternatives. On invention → ask.

## Presenting the choice

After the reasoning prose (citations, what each candidate implies, tradeoffs), present the choice as a lettered menu:

```
[A] - <option A label, brief>
[B] - <option B label, brief>
[C] - Other (type your own answer)
```

The shape of the menu follows the register:

- **Two alternatives** — three options. [A] and [B] are the doc-supported readings; [C] is the custom-input escape hatch.
- **One recommendation** — two options. [A] is the recommendation; [B] is the custom-input escape hatch. Don't pad to three by inventing a weaker [B] — the reason there's only one option is that inventing another would mean reaching outside the corpus.
- **Ask** — no menu. Ask plainly: "Type your answer here." The user types whatever they want.

`defer` and `quit` are text commands the user can type at any prompt; they don't need to appear as menu letters every time. The menu is for the *resolution choice*, not for navigation.

The user types the letter (A / B / C / D as the case may be) for a labeled option, or types a free-text answer that overrides the menu, or types `defer` / `quit`. The agent waits for the response — no timeout, no chaining — before opening the next item.

## Research, when a question is technically researchable

Some questions in `.metis/QUESTIONS.md` are factual gaps the open web can settle, not preference calls. When the question is technically researchable, dispatch the `metis-domain-researcher` subagent rather than punting to the user.

The judgment for *researchable* vs. *user-only*: if the answer would be the same regardless of who you asked (a fact, a benchmark, a published recommendation), it is researchable. If the answer depends on project preferences, business constraints, or values the corpus has not stated, it is the user's to make. A library comparison is researchable; *which library do we want* is the user's call.

The subagent returns its findings inline — no file is written. The substance of the answer goes into the source doc; the `.metis/RESOLVED.md` pointer notes that the resolution turned on research, without citing a research note (there isn't one to cite).

## Asking the user vs. deciding

Default: ask. Most resolutions wait for user confirmation before landing. The agent reads the corpus, frames the choice, and recommends; the user commits.

The narrow exception is filling in a specific value within a shape the corpus has already committed to — picking `400` when the doc says "reject invalid input," naming a log field when the surrounding behavior is pinned, recording an established code path that the docs are silent about. The shape was already decided; the resolution is naming a value inside it.

Anything that picks the shape itself — a response contract, error semantics, a validation rule, a cache strategy, a new constraint downstream code has to live with — is the user's call. When unsure, confirm.

The test: would a thoughtful reader of the source doc say *"this is the answer the doc was already pointing at"*? If yes, auto-land. If they'd say *"this is one of several reasonable readings the doc didn't pin down"* — confirm.

## The source-doc update

Whether the agent lands the edit or the user confirms it, prefer the smallest change that removes the ambiguity the item named. A walk is license to close the specific gap captured, not to rewrite surrounding prose the item didn't force.

## Deferred, resolved, and stale

`deferred` is a conscious "not now." The item stays in its active file with the reason for deferral recorded in the body, so a later walk does not re-offer the same options. It remains open from the walk's perspective — deferral is not a quiet way to archive.

`resolved` means the source doc has been updated so it no longer reads as open. The item is removed from its active file and a pointer is appended to `.metis/RESOLVED.md`.

`stale` is the re-read outcome above: the capture no longer matches the docs. The item stays in its active file until the next reconcile replaces it, or until the user confirms the topic is no longer live.

The three are not interchangeable. Flipping `open` straight to `resolved` without the source-doc update, or collapsing `stale` into `resolved` because the topic seems to have gone away, breaks the property that the on-disk files are the walk's resume state.

## Shape of the resolved pointer

The `.metis/RESOLVED.md` entry is minimal — title, date resolved, and a one-line summary of the answer that was written into the doc:

```markdown
## Q3: Session duration
Resolved: 2026-04-19
Summary: 30-day refresh + 15-min access token.
```

The resolution's substance lives in the updated source doc, not the pointer. The docs themselves are the architectural record going into development; the pointer is only a thin archive trail — what has been resolved — not a second copy of the answer.

## Follow-ups from a walk

A walk can produce new captures, not just close old ones. When a resolution answers the item at hand but exposes a downstream uncertainty — a new term introduced, a consequence that wasn't specified, a sibling question the chosen answer raises — append a fresh item to `.metis/QUESTIONS.md` or `.metis/CONTRADICTIONS.md` for a later pass. Closing one item by quietly hiding the follow-up it spawned is a form of over-resolving.
