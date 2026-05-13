# Honest scope reporting

A scope report is the block that names the places where the shipped work is less than what was asked for. The job of this skill is to take one unit of work — a task that has just finished, a set of changes submitted for review — and render that block: four categories for what was reduced, one-line entries per reduction, and no defense of any of them.

Two failure modes pull against each other. Under-reporting absorbs reductions into the surrounding narrative — "the signature check is in place, edge cases pending" reads as progress when the entry belongs in the scope list as a deferred item. The parent cannot triage what it cannot see. Over-reporting pads the list with reasoning that drifts into defending the reduction — "stubbed the retry logic because the underlying HTTP client is being replaced next sprint" gives the parent a narrative to respond to rather than a reduction to act on. The list gets longer and less useful the more it argues.

## Read first

- The plan, description, or other specification the work is being reported against, so each reduction can be named relative to a criterion a reader can see.
- The diff or change-set the report is summarizing, so entries cite the actual shape that shipped rather than the intent the reporter remembers.

An entry is any place where what shipped diverges from what was asked; the four categories below sort by the kind of divergence.

## Artifact shape

There is no convention file for a scope report. The shape — one block, returned in chat as part of the implementing skill's response — sits here:

- **Skipped** — criteria or scope items that were not addressed and are not planned. One line per entry, naming the criterion.
- **Deferred** — criteria or scope items that were not addressed but are explicitly pending later work. One line per entry, naming the criterion and the follow-up that will carry it.
- **Stubbed** — placeholders that will not behave correctly under real conditions: a function that returns a constant, an error path that raises `NotImplementedError`, a fixture hard-coded where logic was specified, or logic that handles only the sample payload it was built against. One line per entry, naming the placeholder and where it lives.
- **Handled differently** — criteria met by a shape materially different from what the specification named. One line per entry, with the delta spelled out (see below).

An empty report is the common case when the work met its criteria cleanly. Say so in one line — manufacturing entries to fill the block is the mirror image of hiding them.

## Categories are not synonyms

The four categories do different triage work, and collapsing them costs the parent the ability to route. The tests:

- **Skipped** — not done, not planned. The parent decides whether the scope item is dropped, re-opened, or escalated.
- **Deferred** — not done, planned. A follow-up is named concretely in the entry — a task id, a ticket, an explicit pending item; if none can be named, the right category is `Skipped`, not `Deferred`. The parent decides whether that follow-up is acceptable or needs to be promoted.
- **Stubbed** — present in code, not behaving. The parent decides whether the stub ships, gets wrapped in a feature flag, or blocks the merge.
- **Handled differently** — done, but not as written. The parent decides whether the delta is equivalence, tolerable reduction, or a re-open.

When two categories seem to fit, the more specific one wins: a stub that is also explicitly pending later work is `Stubbed` with the pending follow-up named in the entry — the parent needs to know a non-behaving placeholder is in the tree even when there is a plan to replace it. A stub without any follow-up plan is still `Stubbed`, not `Skipped`, because a silent stub and an absent implementation have different downstream consequences.

## List, don't defend

Each entry names *what* was reduced and, where it applies, *what would have to happen* to close it. No entry names *why* the reduction was chosen. The reasoning belongs in the surrounding Notes, in a decision when the choice warrants a standing record, or as a question surfaced upstream — not in the scope list. The list's job is the parent's triage, not the reporter's self-defense. A list crowded with justifications forces the parent to read past each excuse to see the shape of what was reduced; a list without them shows that shape at a glance.

The check: every entry should read as a fact the parent will act on. If a sentence exists to persuade rather than to inform, it belongs elsewhere.

## Handled differently needs the delta spelled out

`Handled differently` is the category that hides without discipline — a reduction phrased as a choice reads like progress until a reader compares it against the original criterion. Each entry in this category names the criterion verbatim from the specification and the shipped behavior in one line, so the parent can tell at a glance whether the shift is equivalence or reduction without re-reading the diff. "Session expiry: spec said 24h sliding window; shipped 24h absolute" is enough. A `Handled differently` entry that paraphrases the criterion buries the delta — if the paraphrase and the shipped behavior both sound reasonable, a reader cannot see what changed.

## Sizing as feedback

A scope report is short by default — typically ~50–250 tokens. A report that runs long is usually narrating the fixes the parent will make or defending the reductions, both of which belong upstream. If every unit of work yields a long report, the upstream sizing or decomposition call is off — surface that observation rather than absorbing it into longer reports.
