# Reviewing against criteria

A review is the check that an implementation meets the description and plan it claims to satisfy. The job of this skill is to take a description, a plan (if one was produced), a diff, and the implementer's scope report, and render a review — per-criterion judgment with specific evidence, a clean separation between code-quality findings and criterion evaluation, and a verdict the caller can act on without re-deriving the work.

Two failure modes pull against each other. Under-rejecting approves a diff that quietly handled a criterion "differently" and lets the scope reduction land silently; a later reader has to re-read the diff to notice what is missing. Over-rejecting blocks a passing diff on nits that should have been noted and moved past; the review becomes tax rather than signal.

## Read first

- The description and plan the implementation was supposed to satisfy, plus the implementer's scope report — all carried in the dispatch prompt.
- The diff under review.
- Source-doc passages the description or plan cites, when a criterion turns on a passage they abbreviated.

The plan is part of the inputs but is not the judgment anchor — see *Reviewing against intent, not plan fidelity* below.

## Artifact shape

The review is returned in chat as one block:

- **Per-criterion findings** — one entry per criterion the description and plan implied, each a pass or fail with specific evidence. Criteria are derived from the inputs (not assumed itemized); the derivation is the reviewer's first job.
- **Scope reduction** — a separate list, present only when the diff delivers less than the description and plan promised. Compare against the implementer's scope report: a reduction the implementer surfaced honestly is one kind of finding; a reduction the report didn't mention is another, more serious one.
- **Code-quality notes** — nits and smells kept out of the criterion findings. Absent when the diff is clean enough to need none.
- **Verdict** — one line: `approve`, `approve-with-nits`, or `reject-with-reasons`.

Sections beyond this belong in conversation around the review.

## Deriving criteria from the inputs

The description names intent (e.g., "implement Stripe webhook signature verification"); the plan names a verification command and a sequence; the scope report names what shipped and what didn't. From these the reviewer derives the criteria a passing implementation has to meet — "rejects invalid signatures with 400," "constant-time compare to prevent timing leaks," "5-minute replay window enforced."

A criterion is a checkable condition. If the description and plan together do not imply a checkable condition, that's an upstream gap — surface it rather than judging the diff against vibes.

## Criterion by criterion, with evidence

Each criterion gets a pass or fail and the specific thing the reviewer pointed at — a test name, a diff hunk, the output of the plan's verification command, a grep result against the repo. "Passes because the code looks right" is not evidence; it is a vibe with a verdict attached. Where the criterion names a visible condition ("returns 400 when the signature is missing"), the evidence is the test or output that shows the condition. Where the criterion is structural ("constant-time compare via `hmac.compare_digest`"), the evidence is the diff line.

A criterion that cannot be evaluated without forming an opinion about the code is not a criterion; it is an underspecified line in the description. Surface that upstream rather than passing the criterion on a reading the reviewer cannot point to.

## Scope reduction is a finding, not a concession

When the implementer's scope report says a criterion was "handled differently" — a stubbed path, a deferred case, a feature toggled off — the reviewer's job is to name that as reduction against the description's intent, not to absorb it into the verdict. The anchor is the description and plan as written when the implementation started; quiet shifts belong in findings.

The test for whether a "handled differently" is reduction or equivalence: can a reader hold the original criterion and the shipped behavior next to each other and see them as the same promise? If no, it is reduction, and the review says so.

When the scope report is silent on a reduction the diff makes, that's a more serious finding — the implementer didn't surface the gap. Flag it explicitly.

## Code quality vs. spec compliance

Two axes. A clean diff does not buy a criterion miss; a code smell does not sink a criterion pass. Nits — naming that reads oddly, a helper that belongs elsewhere, a missed logging opportunity — live in the code-quality notes and adjust the verdict along the approve / approve-with-nits boundary, never the approve / reject boundary. A reviewer who rejects on a nit has confused taste with compliance; a reviewer who approves a criterion miss because the code is otherwise good has done the opposite.

## Verdict

- **approve** — every criterion passes, no scope reduction beyond what the implementer's report surfaced, no nits worth recording. The shortest verdict.
- **approve-with-nits** — every criterion passes, no unsurfaced scope reduction, but code-quality notes are worth leaving behind. The nits are recorded with enough specificity that a follow-up can act on them, and the caller is not blocked.
- **reject-with-reasons** — at least one criterion fails or cannot be evaluated, or the implementer's scope report missed a real reduction. Reasons are specific: the criterion verbatim, the evidence (or its absence) that forced the verdict, and what would have to change for a re-review to pass. A reject that reads as "doesn't feel right" is a review that needs to be rewritten before it is posted.

A verdict that approves while listing reasons that sound like rejects is a reject that flinched. Commit to the verdict the evidence supports.

## Reviewing against intent, not plan fidelity

The judgment anchor is the description's intent (the criteria it implies), not the plan's steps. The plan was the implementer's route to meeting the intent; meeting it is what the review checks. The implementer's scope report may explain a deviation from the plan, and reading that is fair context, but the review is against the intent of the work, not the fidelity of the route. A reviewer who judges the diff against the plan rewards plan fidelity over outcome delivery — the opposite of what the verdict is for.

The practical consequence: when plan and diff diverge but the criteria pass, the review can approve. When plan and diff align but a criterion fails, the review rejects. Plan fidelity does not enter the verdict reasoning in either direction.

## The diff may be empty

The parent's preflight catches the totally-empty case before dispatch. The reviewer may still encounter a diff whose changes are entirely unrelated to the description's surface — a branch with stale work, a hunk that touches the wrong module. When that happens, the right return is not a per-criterion render of fails; it is a finding naming what the diff actually changes and the conclusion that nothing evidences an attempt at the description's intent.

## Sizing as feedback

Short by default — most reviews fit in ~500–1,500 tokens. A review that outgrows the description is either finding scope drift worth surfacing upstream, or editorializing between findings rather than evidencing them. A review under ~150 tokens is usually missing evidence on at least one criterion.
