# Session handoff

`.metis/CURRENT.md` is the handoff note the next session reads first to rehydrate — what happened, where things stand, what's still open, and where to start. The job of this skill is to render that note tightly enough that the fresh session gets oriented from a small, predictable read rather than from the session's transcript.

Two failure modes pull against each other. Under-reporting leaves the next session to re-discover what it needs — "continued on signature verification" reads like a handoff but forces the reader to dig for the state of play. Over-reporting narrates the whole session — every file touched, every decision explored, every aside — and buries the one or two lines the next session actually needs under the ones it doesn't.

## Read first

- The current `.metis/CURRENT.md` being replaced. Writing the next handoff without it makes it easy to re-state still-true context or drop state the previous session flagged as live.

## Artifact shape

There is no convention file for `CURRENT.md`. Four blocks, each with its own judgment:

- **What happened.** Past tense, roughly 100–250 tokens. Load-bearing changes only — the shape that shifted, the surface that landed, the call that got made. A disproven approach the next session would otherwise retry counts; a routine code change already captured in the git log does not. The test is whether the next session needs the line to act, not whether the work was interesting to do. If every file touched in the session makes it into this block, the block is doing the wrong job.
- **Current state.** What's in flight, blocked, or queued, in prose tight enough to pick up from. If a plan was drafted but not yet implemented, the plan (or its key shape) lives here. If implementation is in progress, name the surface and the scope report so far. See *Capturing plans and scope reports* below.
- **Open questions.** One line per question, with enough context that the reader can engage without opening another file. Questions surfaced this session that are still live going forward; questions resolved this session get removed. This is the session-level question list — distinct from `.metis/QUESTIONS.md`, which is for docs-corpus gaps owned by reconcile.
- **Where to start.** Roughly 30–100 tokens of directive prose naming the first action the next session should take. The most load-bearing content in the file — a reader who only has time for one section should be able to pick up work from this one.

## Capturing plans and scope reports

Plans (from `/metis-plan-task`) and scope reports (from `/metis-implement-task`) live in chat by default — they don't have their own files. When a session ends mid-flow, `.metis/CURRENT.md`'s *Current state* block carries enough of the plan or scope report for the next session to resume.

The judgment call is *how much*. A short plan (three or four trivial steps) fits inline. A long plan needs its key shape — the verification command, the two or three load-bearing steps, the open assumptions — captured here, with a pointer that "the full plan was discussed in the prior session" for context the chat history would otherwise have carried. Over-capturing defeats the lean principle the rest of Metis adopted; under-capturing forces the next session to re-derive what the prior session already knew.

The same rule for scope reports: if the implementation finished cleanly, *Current state* notes the close and *Where to start* points at review. If the implementation stopped mid-flow (per the "Knowing when to stop" redline in implement-task), the four-category scope report shape lives here so review can act on it next session.

## Sizing as feedback

Keep `.metis/CURRENT.md` under ~1k tokens. The cap is not aesthetic — rehydration reads this file every new session, and a bloated handoff taxes every one of them. When a draft runs long, two patterns dominate: session history in *What happened* that the next session does not need to act on, and over-captured plan/scope detail in *Current state* that should be a pointer rather than a transcription.

An empty block is fine when there is nothing to report. Manufacturing entries to fill each block is the mirror image of burying state in narrative.
