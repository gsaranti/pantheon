# Metis v0.1 — Project Handoff Document

This document is a complete handoff for the Metis project. It's intended to bring a fresh Claude conversation up to the exact point where design ended, so building can continue without losing context.

Read this document top to bottom. Every section matters. By the end, you should know what Metis is, why it exists, what it's not, what it ships in v0.1, and what's been decided about every meaningful design question.

---

## Table of contents

1. [What Metis is](#what-metis-is)
2. [Why I'm building it](#why-im-building-it)
3. [The existing landscape](#the-existing-landscape)
4. [Metis's positioning and principles](#metiss-positioning-and-principles)
5. [The workflow Metis encodes](#the-workflow-metis-encodes)
6. [Flat and epic layouts](#flat-and-epic-layouts)
7. [Directory structure](#directory-structure)
8. [The command list](#the-command-list)
9. [Conventions](#conventions)
10. [Skills](#skills)
11. [Subagents](#subagents)
12. [Example flows](#example-flows)
13. [Design decisions already made](#design-decisions-already-made)
14. [Build order](#build-order)
15. [What's deferred to v0.2+](#whats-deferred-to-v02)
16. [Open questions](#open-questions)
17. [How to pick up from here](#how-to-pick-up-from-here)
18. [Refinements (post-handoff design conversation)](#refinements-post-handoff-design-conversation)
19. [Appendix: the conversation that produced this](#appendix-the-conversation-that-produced-this)

---

## What Metis is

Metis is an agentic development toolset for Claude Code, oriented around **context management across sessions** as the hard problem. It works on projects of any size and doc-maturity — a flat `tasks/` directory for smaller work, an `epics/` layout for larger builds, with or without an existing docs corpus. It structures the project, not the agent — giving Claude direction, order, and context rather than trying to reshape how Claude thinks or writes.

The core value proposition is simple: at any moment, a fresh agent session can read Metis's on-disk state and know where the project stands — what's planned, what's in progress, what's done, what was decided, and why. How the code actually got written between sessions is orthogonal. The user can code alone, pair with an agent without invoking any Metis commands, use Metis's plan/implement/review loop, or mix all three. Metis's job is to make the next session's context accurate regardless.

It provides:

- A filesystem layout (`BUILD.md`, `epics/` or `tasks/`, `decisions/`, `docs/` reconcile artifacts, `scratch/`, `.metis/`) that makes project state explicit on disk
- Slash commands (`/metis:*`) — some produce those artifacts, some reconcile them against changes the user made outside Metis
- Skills that capture reusable know-how for the agent
- Subagents with scoped tool permissions for task-level execution, when the user wants that structure
- Conventions that standardize file formats

The engineering-loop commands (`/metis:plan-task`, `/metis:implement-task`, `/metis:review-task`) are an option Metis offers, not the spine of Metis. The spine is the artifacts themselves and the reconciliation mechanisms (`/metis:sync`, `/metis:log-work`, hand-editing plus a resync) that keep the artifacts honest when the user bypasses the loop.

The core insight driving the design: **coding agents mostly fail not because they can't write code, but because they lose track of intent across long sessions and silently drift from specs.** Metis counters that failure mode with structure on disk — reconciled specs, task-scoped artifacts, explicit state — and with reconciliation commands that absorb user edits rather than fight them.

The name: Metis is the Greek goddess of wisdom and deep thought, mother of Athena. Tagline candidate: *"Wisdom before code."*

---

## Why I'm building it

### The problem

I'm an engineer who works on medium-to-large projects that typically start with a pile of documentation — UX requirements, design docs, technical specs written at different times, often by different people. The standard "prompt Claude Code to build this" approach breaks down quickly:

- The agent picks one side of a contradiction and runs with it, silently
- Context across sessions degrades — feature 6 doesn't know about decisions made in feature 3
- "Done" is self-reported, not verified
- Scope quietly shrinks; the agent reports the reduced scope as complete
- Architectural drift compounds — a wrong assumption in task 3 becomes a bug in task 17

Existing frameworks address pieces of this but none take "start with a docs directory" as the primary entry point. They assume greenfield or prototype-level work. Metis is for the case where you have substantial specs *before* you start building.

### Why build another framework instead of using existing ones

Several reasons:

1. **None of the existing frameworks center doc reconciliation.** The upstream problem — "I have 80 pages of specs that contradict each other in places" — is where my projects actually start. Superpowers, gstack, and GSD all assume that phase is done.

2. **Existing frameworks are rigid in different ways.** Superpowers enforces TDD at the skill level, forcing the ritual even when it doesn't fit. gstack role-plays the agent through a CEO → PM → QA → engineer arc for every feature, which is theater. GSD is portable but light on opinion.

3. **I want to internalize the design.** Building it myself forces me to actually understand which parts matter and which are ceremony. It also means I can iterate on the shape without waiting for someone else's roadmap.

4. **The "structure the project, not the agent" principle isn't in the current ecosystem.** Existing frameworks try to constrain how the agent thinks. I want something that gives the agent a well-defined task and lets it solve the task however it works best. This is a real positioning gap.

### What success looks like for v0.1

I use it on one real large project end-to-end and it holds up. That's it. No publication, no community, no marketplace. Ship it privately, use it, fix what breaks, then consider publishing.

---

## The existing landscape

Three frameworks I've looked at and the specific thing each does well, plus where Metis differs:

### Superpowers (obra/superpowers)

**What's good**: Principled engineering discipline. TDD enforcement, systematic debugging, verification-before-completion. The subagent-driven development pattern with two-stage review (spec compliance, then code quality) is genuinely good. Skills are the right abstraction and superpowers is the reference for how to write them.

**What's not for me**:
- TDD enforcement is rigid. Forcing RED-GREEN-REFACTOR on every change, including refactors or config work, is ceremony.
- Assumes greenfield. Starts with `brainstorming` skill. Doesn't address the "here's 80 pages of specs" case.
- Heavy prompt weight. The discipline costs tokens even on small changes.

**What Metis borrows**: Two-stage review (implementer + fresh reviewer subagent). Skills as a first-class abstraction. Self-sufficient task files for subagent dispatch.

### gstack (garrytan/gstack)

**What's good**: The `/office-hours` forcing-questions pattern is useful for surfacing what a founder is actually trying to build. Role-based organization fits founder/early-stage workflows well. Event-sourced pipeline mindset.

**What's not for me**:
- The virtual-team metaphor (CEO, PM, QA, Engineer, Designer personas running sequentially per feature) is theater. The model isn't better at code when you tell it "you are the engineer now" — it's better when it has a good plan and clear acceptance criteria.
- Oriented toward product/founder thinking, not engineering rigor on an existing spec.
- 23 skills is too many; most aren't used per feature.

**What Metis borrows**: Personas as exceptions at gates (not per-task). Treating mid-stream feature additions as a first-class operation.

### GSD / get-shit-done (codejunkie99/agentic-stack and related)

**What's good**: Portable — works across many agents (Claude Code, Cursor, Windsurf, Codex, etc.). Memory layers (working/episodic/semantic/personal) and nightly staging cycle for context compression.

**What's not for me**:
- Light on opinion. It's a context system, not a methodology.
- The memory layers are more than I need. `decisions/` as an append-only log is simpler and does the job.
- Portability is not a v0.1 concern — Claude Code is the target.

**What Metis borrows**: Filesystem-as-memory. State on disk, not in session transcripts.

### Google ADK, LangChain, etc.

Different category entirely. These are for building agents, not for structuring how a user works with an agent on a codebase. Not competitors.

---

## Metis's positioning and principles

### Audience

**Engineers using Claude Code on projects where state needs to survive across sessions.**

If the work is a throwaway prototype, a single-session script, or something you won't return to — **Metis is the wrong tool**. The overhead pays off when multiple sessions will touch the same project and you want each one to rehydrate cleanly; without that, the structure is cost without benefit. Tools that know their limits get trusted more.

### The load-bearing opinions

These are Metis's spine. Everything else is convention that can flex:

1. **Structure the project, not the agent.** Metis provides artifacts, conventions, and reconciliation mechanisms. The agent decides how to solve each task. No TDD enforcement, no persona role-play, no prescribed reasoning steps.

2. **Metis is optional at every step; it reconciles, it does not enforce.** Every artifact Metis produces can be hand-edited by the user at any time. The engineering-loop commands (plan/implement/review) are a convenience, not a requirement. The user can code alone, pair with an agent without invoking Metis, or drive work through Metis — and mix freely. Metis's reconciliation commands (`/metis:sync`, `/metis:log-work`, hand-editing followed by a resync) exist to absorb user edits, not to prevent them.

3. **Docs before code, when docs exist.** On a large doc-heavy project, Phase 0 reconciliation pays for itself. The agent reads `docs/`, produces synthesis + contradictions + open questions, and the user walks through them to populate a decisions log before building. This is Metis's strongest recommendation — but a recommendation, not a gate.

4. **Context is task-scoped, not project-scoped.** Every task file is self-sufficient. Subagents work from a task file plus `CLAUDE.md`, the referenced docs, and the parent epic when the task lives under one — never from other task files or `BUILD.md`. State lives on disk, not in session transcripts.

5. **Fresh instances at phase boundaries.** Resumption is for continuity within a phase, not across them. Starting Phase 1 in a fresh instance drops context that would otherwise compound into drift. Metis's artifacts are built to rehydrate a fresh agent quickly.

6. **Decisions are append-only and span the project.** Not buried in task files or docs. `decisions/` is the project's memory across epics and sessions. Superseding happens by writing a new decision, not by editing the old one.

7. **Context efficiency is load-bearing.** Every skill, subagent, and command is authored under a token budget. A Metis-structured session should cost less context than the disorder it prevents. "Works but bloated" is a bug, not a tradeoff; each layer loads only the slice of the conventions it actually needs.

### Tagline candidate

*"Wisdom before code."*

Ties to Metis the goddess (wisdom, deep thought) and to the Phase 0 ethos (reconcile before implementing). Short enough for a README.

### What Metis is not

- Not a general-purpose agent framework (not ADK, not LangChain)
- Not a prototyping tool (use raw prompting)
- Not a replacement for Claude Code (Metis runs *on* Claude Code, leveraging native capabilities like `/init`, plan mode, agentic search)
- Not cross-harness yet (v0.1 targets Claude Code; other harnesses deferred)

### The differentiation from existing frameworks

| Framework | Center of gravity | Metis's difference |
|---|---|---|
| Superpowers | Engineering discipline (TDD, systematic debugging) | Metis is less rigid about *how* the agent works |
| gstack | Product thinking via role-play personas | Metis treats personas as exceptions at gates, not per-task |
| GSD | Portability across agents | Metis is opinionated and Claude Code-first |
| *(gap)* | Starting from existing docs | **This is Metis's wedge** |

---

## The workflow Metis encodes

Metis encodes a canonical four-phase flow for a greenfield doc-heavy project. It is the intended path — the one Metis's artifacts and commands are shaped for — but it is not a gate system. The user can skip phases, reorder them, or bypass the commands entirely and hand-edit artifacts, then run a reconciliation command (`/metis:sync`, `/metis:log-work`) to bring Metis's view back in line. The phases describe *what good looks like*, not what Metis forces.

Phase boundaries are still worth respecting when they're used: each is best started in a fresh Claude Code instance to drop accumulated context that would otherwise compound into drift.

### Phase 0 — Reconcile

Before writing a line of code, the agent reads `docs/` and produces:
- `docs/SYNTHESIS.md` — one-page summary of what the app is, in the agent's own words
- `docs/INDEX.md` — concepts → file + section map
- `docs/CONTRADICTIONS.md` — direct conflicts between docs (doc A says X, doc B says Y)
- `docs/QUESTIONS.md` — gray areas: silences, ambiguities, implicit assumptions, terms used loosely (one thing underspecified vs. two things disagreeing)

Then the user walks through both files with the agent via `/metis:walk-open-items`, one item at a time. For each, the agent offers 1–2 suggested resolutions plus a free-form input option. Each resolution updates the relevant source doc with the chosen answer and moves the item to `docs/RESOLVED.md` as a minimal pointer (title, date, one-line summary of the answer written into the doc). Active files only contain `open` and `deferred` items, so resume is cheap. No `decisions/` entries are written during Phase 0 — the docs being finalized are themselves the project's architectural baseline; decisions start at Phase 1, where changes against that locked baseline need their own record.

Per-item status: `open` (default), `resolved` (moved to RESOLVED.md), `deferred` (still in active file but explicitly skipped for now), `stale` (referenced doc has changed since item was captured — needs re-consideration). The walk supports stop/resume across sessions and non-sequential navigation.

**Phase 0 is always main-agent, not subagents.** Contradictions are cross-document; fragmenting reading across subagents misses them. Subagents may be used as scalpels for compressing a single dense doc or doing a mechanical consistency sweep, but the synthesis and reconciliation stays with the main agent.

**Threshold for hybrid approach**: under 80k tokens total `docs/` size, main agent reads everything. 80k–150k, main agent does a first pass and produces `INDEX.md`, then dispatches subagents to compress the densest docs. Over 150k, hybrid is mandatory and `docs/` itself probably needs pruning.

Token estimation: `wc -w docs/ × 1.3` for prose, × 1.5 for mixed, × 1.8 for schema/code-heavy.

### Phase 1 — Build spec + backlog

From the reconciled docs, produce:
- `BUILD.md` — short (3–8 pages) architecture/build plan in the agent's own words. Data model, modules, integrations, testing approach, first vertical slice.
- Epic breakdown (if the project is going to use epics) or a flat task backlog otherwise
- Task files for the first epic only (if using epics) or the full backlog (flat layout, if small enough)

User edits ruthlessly. The editing pass is the highest-leverage hour of the project.

### Phase 2 — Skeleton

Ship the thinnest end-to-end slice: one route, one screen, one DB write, one passing test, runnable. User drives this directly — too architectural to delegate.

### Phase 3 — Feature loop

The canonical per-task loop, when the user wants Metis's engineering structure:

1. `/metis:pick-task` → choose an unblocked task
2. `/metis:plan-task <id>` → planner subagent produces a plan, user reviews
3. `/metis:implement-task <id>` → main session implements, tests, and closes with real test output and a scope report (per Refinement 10, implementation runs in the main session rather than a subagent)
4. `/metis:review-task <id>` → reviewer subagent judges against acceptance criteria (two-stage review: main-session implementation + fresh-context reviewer)
5. `/metis:scope-check` → agent enumerates what it skipped
6. Merge

This loop is optional. Any task can be coded by the user alone, paired with an agent outside Metis, or partially driven through Metis (e.g., plan by hand, implement interactively, skip the reviewer) and still end up reconciled. `/metis:log-work` absorbs code written outside the loop by diffing the working tree against the task file and updating status, notes, and frontmatter accordingly. Hand-edits to task files are equally legitimate; Metis reads from disk and trusts what it finds there.

Session begins with `/metis:session-start` (loading dose), ends with `/metis:session-end` (update `CURRENT.md`).

Epic boundaries (when the project uses epics): `/metis:epic-retro` writes a retro (flags any scratch worth promoting out for the user to act on), next epic's tasks get generated.

### Pair programming dynamics

Treat the agent as the junior, user as the navigator. Hard rules:
- Ask the agent to defend non-obvious choices before accepting them (`/metis:pushback`)
- Rebaseline every hour or two (`/metis:rebaseline`)
- After every feature, ask what was NOT done (`/metis:scope-check`)
- Keep docs alive — update them in the same PR as implementation reveals truth

---

## Flat and epic layouts

Metis projects take one of two structural shapes. The shape is not a configured mode — it is emergent from what exists on disk. A project that has run `/metis:generate-tasks` has a flat `tasks/` directory; a project that has run `/metis:epic-breakdown` has an `epics/` directory with `EPIC.md` files inside. Commands read the filesystem to know which shape they are dealing with.

There is no `mode:` field in `.metis/config.yaml`, no init-time mode prompt, and no explicit state to keep in sync with the filesystem. The shape is whatever the directories say it is.

### Flat layout

For medium projects with roughly 10–40 tasks that don't need capability-level grouping.

```
tasks/
  0001-*.md
  0002-*.md
  ...
```

No `epics/` directory. No `EPIC.md` files. Just a flat list.

### Epic layout

For large projects with 40+ tasks and work that clusters into capabilities.

```
epics/
  001-authentication/
    EPIC.md
    tasks/
      0001-*.md
      0002-*.md
    retro.md
  002-billing/
    EPIC.md
    tasks/
      ...
```

Directory-per-epic. Tasks nested under their epic. Retro lives with the epic.

### Graduation

`/metis:promote-to-epics` exists for projects that start flat and grow. Takes existing flat tasks, proposes epic grouping, moves files, rewrites paths. The command's preconditions are filesystem-based: it requires a `tasks/` directory at the root and refuses if `epics/` already has content.

### Layout-dependent command behavior

Most commands work the same regardless of shape. A few check the filesystem and behave accordingly:

- `/metis:epic-breakdown` — requires no existing flat `tasks/` content, because its output is an `epics/` scaffold. If flat tasks already exist, errors and points at `/metis:promote-to-epics`.
- `/metis:epic-retro` — requires an `epics/<name>/` directory matching the argument. Errors if the project has no `epics/`.
- `/metis:promote-to-epics` — requires a flat `tasks/` with content and an empty or absent `epics/`. Errors otherwise.
- `/metis:generate-tasks` — with no argument, writes into flat `tasks/` (creates it if absent, assuming no `epics/` is present). With an epic name, writes into `epics/<name>/tasks/`. Errors if the argument shape does not match the filesystem shape.

When a command hits a mismatch, error messages name what's on disk and suggest the likely-correct alternative. Example:

```
This command requires an epics/ directory, but this project has a 
flat tasks/ directory at the root.

If your project has outgrown the flat layout, run:
  /metis:promote-to-epics
```

### Ambiguous state

If both `tasks/` and `epics/` exist at the project root, the layout is ambiguous and the invoked command refuses rather than picking a side. Resolution is user-driven: usually by moving the flat tasks under an epic (or treating them as a pending `/metis:promote-to-epics` run), occasionally by deleting one side if it was created in error.

### What never differs

- The feature loop commands (`/metis:plan-task`, `/metis:implement-task`, `/metis:review-task`, `/metis:scope-check`)
- Session commands (`/metis:session-start`, `/metis:session-end`)
- Maintenance (`/metis:rebaseline`, `/metis:pushback`)

The feature loop is the spine of Metis and is identical regardless of whether the project uses epics.

---

## Directory structure

Two sets of files: project-root artifacts (project's own truth) and `.metis/` (framework scaffolding). Plus `.claude/` for harness integration.

### Full layout (epic-layout example)

```
README.md                  # human onboarding
CLAUDE.md                  # agent operating manual, has a delimited Metis section
BUILD.md                   # canonical "what we're building", from /metis:build-spec

docs/                      # source material
  SYNTHESIS.md             # from /metis:reconcile
  INDEX.md                 # from /metis:reconcile
  CONTRADICTIONS.md        # from /metis:reconcile (open + deferred items only)
  QUESTIONS.md             # from /metis:reconcile (open + deferred items only)
  RESOLVED.md              # archive of Phase 0 resolutions (one-line summary pointers)
  research/                # research notes (auto-dispatched by walk-open-items, build-spec, plan-task)
    INDEX.md               # lookup table for prior research; 60-day staleness window
    <slug>-<YYYY-MM-DD>.md  # one note per investigation
  ... (user's existing docs)

decisions/                 # append-only ADRs, span epics
  2026-04-18-auth-flow.md
  2026-04-19-db-choice.md
  ...

epics/                     # work organized by capability
  001-authentication/
    EPIC.md                # goal, scope, exit criterion
    tasks/
      0001-auth-schema.md
      0002-signup-endpoint.md
      ...
    retro.md               # written at epic close
  002-billing/
    ...

scratch/                   # ephemeral, mostly gitignored
  CURRENT.md               # session handoff (committed)
  questions.md             # running Qs for human (committed)
  plans/                   # subagent-produced plans (gitignored)
    0007.md

.metis/                    # framework scaffolding
  config.yaml              # project settings (spec_version, etc.)
  version                  # Metis version that scaffolded this
  MANIFEST.md              # what Metis created (for uninstall clarity)
  conventions/
    task-format.md
    epic-format.md
    decision-format.md
    frontmatter-schema.md
  templates/
    task.md
    epic.md
    decision.md

.claude/                   # Claude Code integration (harness-specific)
  agents/
    metis/
      task-planner.md
      task-reviewer.md
  skills/
    metis/
      # primary skills (21) — slash-command-invoked, 'name: <command>'.
      # Single-caller references live in each primary's references/ subdir.
      plan-task/
        SKILL.md
      build-spec/
        SKILL.md
        references/
          writing-build-spec.md
      sync/
        SKILL.md
        references/
          propagating-spec-changes.md
      ... (21 primary skills; 7 carry a references/ subdir)

# Plugin-root references (9) — multi-caller and subagent-only.
# Lives outside .claude/, at the plugin root.
references/
  decomposing-build-into-epics.md
  writing-a-task-file.md
  writing-decisions.md
  planning-a-task.md
  doing-domain-research.md
  ... (9 plugin-root references)
```

As of Refinement 12, Metis does not populate `.claude/commands/`. Claude Code still supports that directory (and treats a file at `.claude/commands/deploy.md` as equivalent to `.claude/skills/deploy/SKILL.md`), but Metis's commands live as SKILL.md files. As of Refinement 14, the teaching-register skill layer was dropped — its content became reference markdown documents (per-primary or plugin-root), not skills. Only primary skills register under `.claude/skills/metis/`.

### Flat-layout variation

Replace `epics/` with:

```
tasks/
  0001-*.md
  0002-*.md
  ...
```

Everything else is identical.

### Principle: what goes where

**Project root** — the project's own truth. Would exist in some form even without Metis. `BUILD.md`, `decisions/`, `tasks/` or `epics/`, `docs/`. First-class citizens.

**`.metis/`** — framework scaffolding only. Config, conventions, templates. If Metis is uninstalled, `.metis/` is deleted cleanly and project artifacts remain.

**`.claude/`** — harness integration. Commands, agents, skills in the Claude Code format. Harness-specific; future harnesses would have their own equivalents (`.codex/`, etc.).

Test for placement: *would a user care about this if Metis didn't exist?* If yes, project root. If no, `.metis/`.

### Files Metis creates vs modifies

**Creates fresh**: `BUILD.md`, `decisions/`, `tasks/` or `epics/`, `scratch/`, `.metis/`, `.claude/agents/metis/`, `.claude/skills/metis/` (the 21 primary skills, some with `references/` subdirs), the plugin-root `references/` directory (9 multi-caller and subagent-only references), `docs/SYNTHESIS.md`, `docs/INDEX.md`, `docs/CONTRADICTIONS.md`, `docs/QUESTIONS.md`, `docs/RESOLVED.md`, `docs/research/` (with `INDEX.md`).

**Modifies with delimited sections**: `CLAUDE.md`, `.gitignore`.

### CLAUDE.md delimited section

`CLAUDE.md` may exist already (user-written, auto-generated by Claude Code's `/init`, or from another framework). Metis never clobbers existing content. It uses delimiters:

```markdown
<!-- existing user content stays untouched -->

<!-- metis:start -->
...Metis workflow primer (short overview of layout, key files,
   highlighted write rules, and a pointer to the `/metis:` command set)...
<!-- metis:end -->
```

The block body is shipped at `template/.metis/scripts/claude-block.md` and is the canonical source. `/metis:init`'s script (`.metis/scripts/init.sh`) reads that file at runtime and splices it between the delimiters; on re-run, it replaces only the body between the markers, preserving user edits elsewhere in `CLAUDE.md`. Editing the block content means editing `claude-block.md` — this doc is not the source.

### .gitignore additions

```gitignore
# <!-- metis:start -->
...scratch-ignore rules (ignore ephemeral contents, keep the
   load-bearing files like scratch/CURRENT.md and scratch/questions.md)...
# <!-- metis:end -->
```

The block body is shipped at `template/.metis/scripts/gitignore-block.txt` and is the canonical source. Same splice mechanics as `CLAUDE.md`.

---

## The command list

Twenty-two commands total. All namespaced as `/metis:<name>` to avoid collisions with Claude Code built-ins and other frameworks.

### Setup (4)

- **`/metis:init`** — scaffold the Metis directory structure (`.metis/`, `.claude/`, `scratch/`, the delimited section in `CLAUDE.md` and `.gitignore`). Does not ask whether the project will use epics — that emerges from whether the user later runs `/metis:generate-tasks` (flat) or `/metis:epic-breakdown` (epics). Non-destructive; preserves existing files via delimited sections.
- **`/metis:reconcile [prompt]`** — read `docs/`, produce `docs/SYNTHESIS.md`, `docs/INDEX.md`, `docs/CONTRADICTIONS.md`, and `docs/QUESTIONS.md`. Surfaces both contradictions (direct conflicts) and gray areas (silences, ambiguity, underspecification). Requires `docs/` to exist.
- **`/metis:walk-open-items [prompt]`** — walk through open items from both `docs/CONTRADICTIONS.md` and `docs/QUESTIONS.md` one at a time. For each item, agent offers 1–2 suggested resolutions plus a free-form user-input option. Supports stop/resume across sessions via per-item status (`open` / `resolved` / `deferred` / `stale`); resolved items are moved to `docs/RESOLVED.md` immediately so the active files stay lean. Each resolution updates the relevant source doc and appends a minimal pointer to `RESOLVED.md`. No `decisions/` entries are written — Phase 0 finalizes the baseline the docs speak for; decisions start at Phase 1.
- **`/metis:build-spec [prompt]`** — produce `BUILD.md`. Reads `docs/` + `decisions/` if they exist; accepts optional prompt as alternative or supplement.

### Planning (4)

- **`/metis:epic-breakdown`** — propose 8–15 epics from `BUILD.md` and create the `epics/` scaffold (one directory per epic with an `EPIC.md` inside) after approval. Refuses if a flat `tasks/` directory already has content; points at `/metis:promote-to-epics` instead.
- **`/metis:generate-tasks [epic]`** — generate task files. With no argument, populates a flat `tasks/` directory (creates it if absent). With an epic name, populates `epics/<name>/tasks/`. Errors if the argument shape does not match the filesystem shape (e.g. passing an epic name in a flat-`tasks/` project, or omitting it when only `epics/` exists).
- **`/metis:feature <description>`** — describe a new feature mid-stream. Produces feature spec and task files. Works regardless of whether the project uses epics.
- **`/metis:skeleton-plan`** — plan the thinnest end-to-end slice. Read-only.

### Feature loop (5)

- **`/metis:pick-task`** — list unblocked, prioritized tasks.
- **`/metis:plan-task <id>`** — dispatch `task-planner` subagent. Does not write code.
- **`/metis:implement-task <id>`** — implement a task in the main session. Loads the task file, the parent `EPIC.md` if the task lives under one, the approved plan at `scratch/plans/<id>.md` if present, and only the docs in `docs_refs`. Writes land in the assigned task file (status → `in-review`, appended Notes) and the code it touches; `BUILD.md`, `scratch/CURRENT.md`, `decisions/`, and other task files are off-limits as prompt-level discipline. Closes with a scope report per `honest-scope-reporting`. Not a subagent — see §Refinement 10.
- **`/metis:review-task <id>`** — dispatch `task-reviewer` subagent. Judges against acceptance criteria.
- **`/metis:scope-check`** — ask agent to enumerate what it skipped or reduced, no justification.

### Sessions (4)

- **`/metis:session-start`** — fresh-instance loading dose (`CLAUDE.md`, `CURRENT.md`, active task file).
- **`/metis:session-end`** — update `scratch/CURRENT.md`, flag promotions out of `scratch/`.
- **`/metis:rebaseline`** — drift detector. Read-only. Compares current state of `docs/`, `BUILD.md`, and `epics/`/`tasks/` against a lightweight baseline (git markers + frontmatter `doc_hash` / `spec_version`) and reports what changed and which downstream artifacts reference it. Does not write.
- **`/metis:pushback`** — ask agent to defend its last choice.

### Change management (2)

- **`/metis:sync [prompt]`** — write counterpart to `/metis:rebaseline`. Reconciles *spec drift*: when source docs, `BUILD.md`, or epics have changed, walks proposed cascading updates one at a time (doc change → propose `BUILD.md` edit → on approval, propose epic edits → propose task edits). Every accepted change appends a `decisions/` entry. Never auto-applies. Main-agent (not subagent) work — cross-document reasoning. Cascade rules: `done` tasks don't update in place (changes become new tasks or superseding decisions), `pending`/`in-review` edit in place, `in-progress` requires confirmation. Batches simple textual updates; walks substantive ones interactively.
- **`/metis:log-work [task-ids] <description>`** — reconciles *implementation drift*: records code work the user did outside Metis (hand-edits, hotfixes, experiments). Runs `git diff` to verify; user's natural-language description is the source of truth for intent, the diff is the source of truth for what happened. Updates task statuses, appends Notes, handles task CRUD (split/merge/add). With no task argument, creates a retroactive `done` task from the diff + description.

### Epic boundaries (1)

- **`/metis:epic-retro <epic>`** — write `retro.md` for a finished epic. Requires a matching `epics/<name>/` directory; errors if the project has no `epics/`.

### Maintenance (1)

- **`/metis:promote-to-epics`** — graduate flat → epic layout by grouping existing tasks into proposed epics. Requires a flat `tasks/` with content and an empty or absent `epics/`; errors otherwise.

### Command-to-skill-to-subagent mapping

| Command | Uses skill(s) | Dispatches subagent |
|---|---|---|
| `/metis:init` | — | — |
| `/metis:reconcile` | `reconciling-docs` | — |
| `/metis:walk-open-items` | `walking-open-items` | `domain-researcher` (when a question is researchable) |
| `/metis:build-spec` | `writing-build-spec` | `domain-researcher` (when the corpus has technical gaps) |
| `/metis:epic-breakdown` | `decomposing-build-into-epics`, `writing-an-epic-file` | — |
| `/metis:generate-tasks` | `decomposing-work-into-tasks`, `writing-a-task-file` | — |
| `/metis:feature` | `decomposing-work-into-tasks`, `writing-a-task-file`, `decomposing-build-into-epics`, `writing-an-epic-file` | — |
| `/metis:skeleton-plan` | — | — |
| `/metis:pick-task` | — | — |
| `/metis:plan-task` | — | `task-planner` (which dispatches `domain-researcher` when a plan-step gap surfaces) |
| `/metis:implement-task` | `planning-a-task`, `writing-a-task-file`, `honest-scope-reporting` | — |
| `/metis:review-task` | — | `task-reviewer` |
| `/metis:scope-check` | `honest-scope-reporting` | — |
| `/metis:session-start` | — | — |
| `/metis:session-end` | `session-handoff` | — |
| `/metis:rebaseline` | — | — |
| `/metis:pushback` | — | — |
| `/metis:sync` | `propagating-spec-changes`, `writing-decisions` | — |
| `/metis:log-work` | `logging-external-work`, `writing-decisions` | — |
| `/metis:epic-retro` | `writing-retros` | — |
| `/metis:promote-to-epics` | `decomposing-build-into-epics`, `writing-an-epic-file` | — |

Skills are thin wrappers around the references they load. References carry the artifact-shape teaching. Subagents provide clean context + tool restrictions for task-level execution. As of Refinement 14, the teaching-register skill layer was dropped — references are markdown documents loaded by file path, not first-class skills.

### Error messages on layout mismatch

Commands that check filesystem layout should produce helpful errors. Each error names what's on disk and points at the likely-correct alternative:

```
This command requires an epics/ directory, but this project has a 
flat tasks/ directory at the root.

If your project has outgrown the flat layout, run:
  /metis:promote-to-epics

Otherwise, you probably want:
  /metis:generate-tasks
```

Helpful errors with the likely-correct alternative. Not "wrong layout, goodbye."

---

## Conventions

Five files at `.metis/conventions/`. They define the canonical on-disk formats and cross-artifact conventions Metis relies on. Conventions are a **human- and design-time reference as well as a runtime one**: they encode shapes and conventions so both the user and Metis's agents agree on what those files mean. Runtime skills, subagents, and commands each carry only the slice they need rather than bulk-loading every convention per session.

(A sixth document, `write-rules.md`, originally lived alongside these but was moved to `docs/metis-write-rules.md`. It is a design-time narrative about who-writes-where and the framework's layer responsibilities, not a file-format spec; it is never referenced by a skill at runtime, so keeping it in the runtime conventions folder was misleading. See "Write rules (design-time reference)" below. The convention that *is* load-bearing at runtime — how commands and subagents handle the optional trailing free-text prompt — lives at `.metis/conventions/command-prompts.md`; see Refinement 12.)

### `task-format.md`

Specifies task file structure:
- Frontmatter fields (see `frontmatter-schema.md`)
- Section order: Goal, Context (excerpted), Scope boundaries, Acceptance criteria, Expected file changes, Notes
- Sizing: ~400–1200 words. Longer means split.
- Excerpting rule: quote doc sections directly, don't just link
- When the task lives under an epic, the parent `EPIC.md` is part of every task's implicit context (readers load it alongside the task file)

Task files are stable by default, not immutable: the user may edit any field by hand. The `id` and `title` are expected to stay fixed once a task is underway because other artifacts refer to them, but changing them is a supported workflow — reconcile via `/metis:log-work` or a direct resync, not by forbidding the edit.

### `epic-format.md`

Specifies `EPIC.md` structure:
- Frontmatter: name, goal, status, exit criterion, dependencies
- Sections: Goal, Scope, Out-of-scope, Exit criterion, Notes
- Sizing: ~1 page
- No strict task-count range. Epics cluster around a single testable exit criterion; task volume follows from the work, not from a quota.

### `decision-format.md`

ADR template for `decisions/` entries:
- Filename: `YYYY-MM-DD-kebab-case-title.md`
- Sections: Date, Context, Decision, Consequences, Evidence (optional)
- One paragraph per section, sometimes more
- Append-only — superseding is done by writing a new decision whose Context names the old one

Decisions are written by `/metis:sync`, `/metis:log-work`, and by the main session whenever a change to `BUILD.md` or a source doc warrants a standing record. Phase 0 walks (`/metis:walk-open-items`) do not write decisions — they finalize the docs that are themselves the architectural baseline, so there are no changes-against-baseline yet to record. Subagents do not write decisions.

### `frontmatter-schema.md`

Canonical YAML frontmatter fields:

```yaml
---
id: "0007"                    # zero-padded 4-digit STRING (quoted — YAML parses 0007 as int 7)
epic: 002-billing             # present only when the task lives under epics/<name>/tasks/
title: Stripe webhook handler
status: pending | in-progress | in-review | done | blocked
priority: 1-5
depends_on: ["0003", "0005"]  # list of task ID strings (quoted)
estimate: small | medium | large
touches: [src/billing/, src/api/webhooks.ts]
docs_refs:
  - docs/billing.md#webhook-events
  - docs/security.md#webhook-verification
doc_hashes:                   # for drift detection by /metis:rebaseline + /metis:sync
  docs/billing.md: a3f1c9...
  docs/security.md: 7b2e44...
spec_version: 3               # bumps when BUILD.md sections this task references change
---
```

Specifies what's required vs optional, what values are valid, and why each field exists. The `doc_hashes` and `spec_version` fields support drift detection — when a referenced doc or `BUILD.md` section changes, the task is flagged stale by `/metis:rebaseline` and offered for cascade by `/metis:sync`.

### `command-prompts.md`

Canonical source for how a Metis skill or subagent handles the optional trailing free-text prompt a user can type after a slash invocation. Carries the four discipline rules (augment / flag scope expansion / acknowledge use / resolve named skills) and the ephemerality rule. Nothing more — the convention does not look up at its callers; it does not prescribe how skills reference it, nor enumerate which skills do and don't.

Added in Refinement 12. Lives in `.metis/conventions/` rather than `docs/` because runtime artifacts (skills, subagents) need to reference it, and runtime files may not reach into `docs/`. Of the 22 command-register skills, the 15 that accept a trailing prompt point at this file; the 7 mechanical skills (see the handoff's §The command list and the §On commands bullet naming them) silently accept and ignore trailing prompts and do not reference the convention. Both subagents reference it.

### Write rules (design-time reference, lives in `docs/metis-write-rules.md`)

A design-time reference for who writes what. Captures the rules as a whole so the design stays legible; the actual enforcement lives in the individual skill and subagent prompts, which each carry the one or two rules they need. Lives in `docs/` rather than `.metis/conventions/` because no skill loads it at runtime — it is framework-author reading, not a file-format spec a runtime artifact consults. Highlights:

- Only the parent/main session writes to `scratch/CURRENT.md`
- Subagents write only to their assigned task file and their return value
- Decisions go in `decisions/`, never in scratch; they are append-only
- `BUILD.md` changes only with an accompanying decision entry
- Task files are stable by default but the user can hand-edit any field; Metis reconciles edits via `/metis:log-work` or a resync rather than forbidding them
- When a doc in `docs/` changes, update `BUILD.md` if relevant and log a decision entry
- Resolved items from `CONTRADICTIONS.md` / `QUESTIONS.md` move to `docs/RESOLVED.md` as minimal pointers; `RESOLVED.md` is never loaded during a walk unless explicitly requested

It also defines the **command-prompts convention** (an optional trailing free-text argument to most substantive commands) and three discipline rules for it: augment-not-replace, flag-scope-expansion, and acknowledge-use-explicitly. The prompt is ephemeral — never persisted to disk. Individual commands and subagents pick up this convention on their own; the file is the single source that documents it.

---

## References

References are markdown documents the skills load at runtime via file path. They are not first-class skills — they don't appear in the user's slash-command surface. The content is artifact-shaped teaching: how to write a task file, when to split, how to scope research, etc. See Refinement 14 for the restructure that produced this layer.

Two locations:

- **Per-primary references** (`.claude/skills/metis/<primary>/references/<name>.md`) — used by exactly one primary skill, lives next to it.
- **Plugin-root references** (`references/<name>.md`) — used by multiple primary skills, or read by a subagent.

### Per-primary references (7)

| Reference | Belongs to | Covers |
|---|---|---|
| `writing-build-spec.md` | `/metis:build-spec` | The brief's shape — risk-first framing, own-words rule, first vertical slice, sizing, citing research findings |
| `walking-open-items.md` | `/metis:walk-open-items` | Walking one item — alternatives/recommendation/ask register, asking-the-user threshold, source-doc update, lifecycle states, dispatching research for technically-researchable questions |
| `writing-retros.md` | `/metis:epic-retro` | Four retro blocks (estimation, replans, assumption failures, task-breakdown lessons), per-task discipline, sizing |
| `propagating-spec-changes.md` | `/metis:sync` | Cascade detection, cosmetic-vs-substantive, status-aware rules, decision-per-accepted-change, termination |
| `reconciling-docs.md` | `/metis:reconcile` | Detection (contradictions vs gray areas), surfacing without resolving, stale detection on re-reconcile |
| `logging-external-work.md` | `/metis:log-work` | git diff vs description as dual sources, per-task claim types (done/progress/CRUD), retroactive tasks, architecture-trigger heuristics |
| `session-handoff.md` | `/metis:session-end` | The four blocks of `CURRENT.md`, pruning `questions.md`, sizing |

### Plugin-root references (9)

| Reference | Used by |
|---|---|
| `decomposing-build-into-epics.md` | `/metis:epic-breakdown`, `/metis:feature`, `/metis:promote-to-epics` |
| `decomposing-work-into-tasks.md` | `/metis:generate-tasks`, `/metis:feature` |
| `writing-a-task-file.md` | `/metis:generate-tasks`, `/metis:feature` |
| `writing-an-epic-file.md` | `/metis:epic-breakdown`, `/metis:feature`, `/metis:promote-to-epics` |
| `writing-decisions.md` | `/metis:sync`, `/metis:log-work` |
| `honest-scope-reporting.md` | `/metis:implement-task`, `/metis:scope-check` |
| `planning-a-task.md` | `task-planner` subagent, `/metis:implement-task` |
| `reviewing-against-criteria.md` | `task-reviewer` subagent |
| `doing-domain-research.md` | `domain-researcher` subagent |

References are loaded by relative file path from the calling SKILL.md or subagent .md. Per-primary uses `references/<name>.md`; plugin-root from a primary skill uses `../../references/<name>.md`; plugin-root from a subagent uses `../references/<name>.md`. The path conventions are documented in `docs/metis-write-rules.md`.

## Subagents

Two subagents at `.claude/agents/metis/<name>.md`: `task-planner` and `task-reviewer`. Each has tool restrictions that enforce workflow properties structurally rather than through prompt discipline. The third task-level command in the feature loop, `/metis:implement-task`, runs in the main session rather than a subagent — see Refinement 10 for the reasoning. Its discipline (load list, write scope, return shape, invocation-prompt rules) is carried by the command prompt rather than a subagent system prompt.

### `task-planner`

**Purpose**: Read a task file, produce an implementation plan. No code changes.

**Tools**: `Read`, `Glob`, `Grep`, `Write` (restricted to `scratch/plans/`).

**Uses reference**: `references/planning-a-task.md` (loaded as `../references/planning-a-task.md` from agents/).

**System prompt covers**:
- Who they are (fresh context, no parent memory)
- What to load (the specified task file, the parent `EPIC.md` when the task lives under one, only the docs in `docs_refs`)
- What NOT to read (other task files, `BUILD.md`, other epics)
- What to produce (plan at `scratch/plans/<id>.md`)
- What to return (plan summary + flagged ambiguities)

**Why the tool restriction**: can't start implementing while planning. Enforced structurally.

### `task-reviewer`

**Purpose**: Review a diff against acceptance criteria.

**Tools**: `Read`, `Glob`, `Grep`, `Bash` (for running `git diff` and tests only, no mutating commands).

**Uses reference**: `references/reviewing-against-criteria.md` (loaded as `../references/reviewing-against-criteria.md` from agents/).

**System prompt covers**:
- Fresh context — the reviewer didn't write the code, has no ego
- What to load (task file including acceptance criteria, parent `EPIC.md` when the task lives under one, git diff, implementer's return notes; `CLAUDE.md` is auto-loaded)
- What NOT to load (the plan — we want judgment against the task file, not compliance with the plan)
- Evaluation per acceptance criterion: pass/fail + evidence (file/line citations)
- Separate code quality from spec compliance
- Return: verdict (approve / approve-with-nits / reject-with-reasons) + findings

**Why the tool restriction**: read-only means reviewer can't "helpfully fix" — must report findings. Prevents the reviewer from becoming a second implementer.

### `domain-researcher`

**Purpose**: Investigate one technical question against the open web; produce a research note in `docs/research/`.

**Tools**: `Read`, `Glob`, `Grep`, `WebSearch`, `WebFetch`, `Write` (restricted to `docs/research/`).

**Uses reference**: `references/doing-domain-research.md` (loaded as `../references/doing-domain-research.md` from agents/).

**System prompt covers**:
- Fresh context with web tools and read-only access to project files passed in
- What to load (the question, sub-questions, the *why* the parent passed through, project constraints, `docs/research/INDEX.md` for prior-art check)
- What NOT to load (full source-doc corpus, decision entries wholesale, BUILD.md beyond cited section, scratch beyond what the parent passes)
- Investigation discipline (time-box, cite every claim, surface tradeoffs not preferences, explicit confidence, anchor to the project not the technique)
- Two write targets: the research note at `docs/research/<slug>-<YYYY-MM-DD>.md` and an append to `docs/research/INDEX.md`
- Return: note path, top recommendation with confidence, options named, open questions

**Why the subagent shape**: web research generates piles of intermediate noise (every search result, every fetched page). A subagent does the heavy reads in fresh context and returns a compressed note; the parent's context grows by the synthesized artifact, not by everything the agent read to make it. Tool restriction also matters — the researcher has web access but cannot mutate the project corpus.

**System prompt covers**:
- Fresh context — the reviewer didn't write the code, has no ego
- What to load (task file including acceptance criteria, parent `EPIC.md` when the task lives under one, git diff, implementer's return notes; `CLAUDE.md` is auto-loaded)
- What NOT to load (the plan — we want judgment against the task file, not compliance with the plan)
- Evaluation per acceptance criterion: pass/fail + evidence (file/line citations)
- Separate code quality from spec compliance
- Return: verdict (approve / approve-with-nits / reject-with-reasons) + findings

**Why the tool restriction**: read-only means reviewer can't "helpfully fix" — must report findings. Prevents the reviewer from becoming a second implementer.

### Handling invocation prompts (both subagents)

Each subagent accepts an optional free-text prompt from the dispatching command (e.g., `/metis:plan-task 0007 "focus on retry semantics; the existing code uses tenacity, follow that pattern"`). Discipline rules baked into every subagent's system prompt:

1. **Augment, don't replace.** The invocation prompt augments the task file. The task file remains authoritative. If the prompt genuinely contradicts the task file (e.g., "ignore the acceptance criteria for test coverage"), the subagent flags the conflict and asks rather than silently choosing.

2. **Flag scope expansion.** If the prompt asks for something that expands scope beyond the task file, the subagent notes it in its return rather than quietly doing it. Same honest-scope-reporting discipline, applied in the other direction.

3. **Acknowledge use explicitly.** The subagent's return states how the prompt was used so it's traceable after the fact. Example: "Per your note to use tenacity, I followed the existing retry pattern in `billing/client.py` rather than implementing from scratch."

These rules also apply to main-agent commands that accept a prompt (`/metis:reconcile`, `/metis:walk-open-items`, `/metis:build-spec`, `/metis:implement-task`, `/metis:sync`, `/metis:log-work`, `/metis:epic-breakdown`, `/metis:epic-retro`). The prompt is ephemeral; it is never persisted to disk.

### Subagent composition with skills

The relationship:

- **Subagent** = container (system prompt, tools, identity)
- **Skills** = capabilities invoked within the subagent's context

A subagent's system prompt references skills it should use. Skills activate within the subagent's fresh context and guide its behavior. Subagents invoke skills by reference — the system prompt names the skills relevant to the job and the agent reads the SKILL.md on demand, rather than inlining skill content into the subagent prompt or bulk-loading every skill at startup. The same invoke-by-reference pattern applies to main-agent commands; whether a given skill is invoked from a subagent or from the main session is a property of the calling command, not of the skill.

---

## Example flows

### Epic layout, docs-first, greenfield

The canonical Metis flow.

**Setup** (fresh instance per step):

1. `/metis:init` → scaffold the Metis directories (no mode question — the layout emerges from later commands)
2. `/metis:reconcile` → synthesis + contradictions
3. `/metis:walk-open-items` → resolve each contradiction and open question, finalize the docs
4. `/metis:build-spec` → `BUILD.md`
5. `/metis:epic-breakdown` → propose epics, user edits, commit
6. `/metis:generate-tasks 001-<name>` → task files for first epic only
7. `/metis:skeleton-plan` → plan the end-to-end slice
8. Implement the skeleton directly

**Feature loop** (repeats per task):

9. `/metis:session-start`
10. `/metis:pick-task`
11. `/metis:plan-task 0007` → review plan
12. `/metis:implement-task 0007`
13. `/metis:review-task 0007`
14. `/metis:scope-check`
15. Merge
16. `/metis:session-end`

Occasionally: `/metis:rebaseline`, `/metis:pushback`.

**Epic boundary** (once per finished epic):

17. `/metis:epic-retro 001-<name>`
18. `/metis:generate-tasks 002-<name>` → start next epic

**Mid-stream addition**: `/metis:feature "..."` when new requirements emerge.

### Flat layout, docs-first

For medium projects.

1. `/metis:init` → scaffold
2. `/metis:reconcile` (skip if `docs/` is thin)
3. `/metis:walk-open-items` (skip if no open items)
4. `/metis:build-spec`
5. `/metis:generate-tasks` (no epic argument — writes into flat `tasks/`)
6. `/metis:skeleton-plan`, implement skeleton
7. Feature loop (same as epic layout, no epic ceremony)
8. Periodic `/metis:rebaseline`
9. `/metis:promote-to-epics` if the project outgrows the flat layout

### Flat layout, prompt-seeded, no docs

The weakest starting point, but supported.

1. `/metis:init` → scaffold
2. `/metis:build-spec "a task-tracking app with auth, teams, and weekly digest emails"` → agent asks clarifying questions, produces `BUILD.md`
3. `/metis:generate-tasks`
4. Skeleton + feature loop as above

### Existing codebase, no docs

Simplified in v0.1 (no dedicated `/metis:explore`). Relies on Claude Code's native exploration.

1. `/metis:init` → scaffold
2. `/metis:build-spec "add SSO and billing on top of the existing codebase"` → agent explores the codebase natively, reads relevant code, asks clarifying questions, produces `BUILD.md` describing what to build (not what exists)
3. `/metis:generate-tasks` (flat layout) or `/metis:epic-breakdown` + `/metis:generate-tasks <epic>` (epic layout) — pick based on expected size
4. Feature loop — each task's `docs_refs` can point at code paths as well as docs

---

## Design decisions already made

These were worked through in conversation and shouldn't be re-opened unless new information emerges.

### On framework positioning

- **Metis is a toolset, not a workflow.** Its value is context maintenance across sessions — a fresh agent can read on-disk state and know where the project stands. The engineering-loop commands (plan/implement/review) are optional.
- **Targeting engineers with large doc-heavy projects.** Explicit audience.
- **"Structure the project, not the agent"** is the load-bearing principle.
- **Seven opinions are the spine**: structure-project-not-agent; Metis-is-optional; docs-before-code when docs exist; task-scoped-context (including parent `EPIC.md` when the task lives under one); fresh-instances-at-boundaries; append-only-decisions; context-efficiency.
- **The user retains full control.** Every artifact Metis produces can be hand-edited. Reconciliation (`/metis:sync`, `/metis:log-work`) absorbs user edits rather than fighting them.
- **Context efficiency is a design constraint, not a polish task.** Skills, subagents, commands, and conventions are each authored under a token budget. Each layer loads only the slice of the conventions it actually needs.
- **Not building cross-harness support in v0.1.** Claude Code only.
- **Not building lite/heavy modes.** Metis is the heavy-structure option; people who want lighter should use something else.

### On project layout

- **Two layouts: flat and epic.** Emergent from filesystem state rather than a configured mode. A project has a flat `tasks/` or an `epics/` directory; commands read the filesystem to know which they are dealing with. There is no `mode:` field in `.metis/config.yaml`.
- **Flat is the implicit default.** A bare `/metis:init` scaffolds nothing layout-specific. The first of `/metis:generate-tasks` or `/metis:epic-breakdown` creates the shape.
- **No sub-epics.** Subtasks live as checklists inside task files. If a "subtask" deserves its own file, it's actually a task.
- **Commands check filesystem state and error with helpful alternatives when invoked in the wrong shape.** See §Layout-dependent command behavior for the specific checks each command performs.

### On commands

- **All commands namespaced `/metis:*`** to avoid collisions.
- **`/metis:init` is non-destructive.** Uses delimited sections in `CLAUDE.md` and `.gitignore`. Preserves existing content.
- **`/metis:generate-tasks` takes an epic-name argument when the project has an `epics/` directory and no argument when it has a flat `tasks/`.** Errors if the argument shape does not match the filesystem shape.
- **`/metis:init` is run last in build order** because it scaffolds everything else; knowing what "everything else" looks like helps.
- **Commands are thin wrappers over teaching skills and subagents.** ~500–1200 words each. Heavy lifting in teaching skills and conventions.
- **Commands live as SKILL.md files** under `.claude/skills/metis/metis-<name>/` with `name: metis:<name>` and `disable-model-invocation: true` — see Refinement 12. The command/skill distinction is content register; the `metis-` directory prefix is a filesystem-readable hint to the same distinction, so a browse of `.claude/skills/metis/` shows the 22 top-level commands grouped together at the top of an alphabetized list.

### On directory layout

- **`.metis/` holds framework scaffolding only** (config, conventions, templates).
- **Project-root holds project's own truth** (`BUILD.md`, `tasks/` or `epics/`, `decisions/`, `docs/`, `scratch/`).
- **Test for placement**: "would a user care about this if Metis didn't exist?"
- **`.claude/` is harness-specific** (commands, agents, skills). Future harnesses would have `.codex/`, etc.
- **`BUILD.md` is always forward-looking** — what we're building. Never backward-looking (what exists). Existing-codebase mode would need a separate artifact (deferred to v0.2).

### On workflow

- **Phase 0 through Phase 2 are separate fresh instances.** Resume within a phase, not across. State survives via committed files, not session transcripts.
- **Phase 0 reconciliation is main-agent by default.** Subagents are scalpels for compressing single dense docs or mechanical consistency sweeps, not for the reconciliation itself.
- **Hybrid Phase 0 threshold**: 80k tokens total `docs/` size. Under 80k, main agent reads everything. 80k–150k, hybrid. Over 150k, hybrid mandatory + probably prune `docs/`.
- **Token estimation**: `wc -w × 1.3` for prose, × 1.5 for mixed, × 1.8 for schema/code-heavy.
- **Fresh Claude Code instance per phase.** State on disk, not in transcript. `/clear` is the closest thing to "new instance without restarting."
- **Generate task files for the first epic only** after epic breakdown. You'll learn from the first epic things that should change how later epics are broken down.

### On subagents

- **Two subagents in v0.1**: `task-planner` and `task-reviewer`. `/metis:implement-task` runs in the main session rather than a subagent (Refinement 10).
- **Tool restrictions enforce workflow properties for the two subagents.** Planner can't edit code. Reviewer is read-only.
- **Two-stage review** (main-session implementation + fresh-context reviewer subagent) is standard for non-trivial tasks. The independence comes from the reviewer's fresh context, not from the implementer being a subagent.
- **Subagent briefs are self-sufficient.** Task file + CLAUDE.md (auto-loaded) + referenced docs + parent `EPIC.md` (when the task lives under one) is enough context. If it's not, the task file is underspecified.

### On skills vs conventions

- **Conventions = what** (schemas, formats, rules). Static reference.
- **Skills = how** (judgment, patterns, best practice). Applied know-how.
- **Skills reference conventions.** Users and agents can read either.

### On existing codebases

- **No `/metis:explore` in v0.1.** Claude Code's native exploration is used via `/metis:build-spec` with a prompt.
- **No `docs/SYSTEM.md`-style artifact in v0.1.** Agent explores on demand per task.
- **`/metis:explore` and dedicated existing-codebase artifacts are v0.2 targets.**

### On prompts

- **Fresh-instance prompts need explicit load blocks.** Same-instance prompts can reference prior conversation.
- **Every prompt specifies what NOT to read** as much as what to read.
- **Demand real output, not claims** ("show me test output" not "run the tests").
- **Ask for self-critique before user critique.**

---

## Build order

Build from the deepest layer outward. Each layer depends only on what's below it. **Complete each layer in full before starting the next.**

### Order

1. **Conventions** (4 files). Everything else depends on these: `task-format.md`, `epic-format.md`, `decision-format.md`, `frontmatter-schema.md`. (A separate design-time reference, `docs/metis-write-rules.md`, captures the framework's layer responsibilities and who-writes-where rules; it informs how the skills and commands are written but is not itself loaded at runtime.)
2. **Templates** (3 files). Directly instantiate the conventions — `task.md`, `epic.md`, `decision.md` — and serve as canonical starting points for each artifact type. Built immediately after conventions because writing the templates solidifies the convention spec by making it concrete.
3. **Skills** (15 skills). The substance of agent behavior. Each skill is a directory with `SKILL.md` plus an `examples/` folder. Examples are critical — skills without examples are hand-wavy.
4. **Subagents** (2 subagents). Containers that compose skills + tool restrictions: `task-planner` and `task-reviewer`. (The third task-level command, `/metis:implement-task`, is built in the commands layer rather than as a subagent — see Refinement 10.)
5. **Commands** (22 command-register SKILL.md files). Thin wrappers that dispatch subagents or invoke teaching skills. File-format-wise these are skills — `.claude/skills/metis/<name>/SKILL.md` with `name: metis:<name>` and `disable-model-invocation: true`; see Refinement 12 — but the content register (orchestration, not artifact-teaching) is what sets them apart. **Within this step, `/metis:init` is built last** because it scaffolds everything else; knowing what "everything else" looks like helps.

### Why layer-by-layer instead of vertical slice

An earlier draft of this section recommended building the smallest vertical slice first (one convention + one skill + one command) to validate the convention → skill → command relationship before investing in 22 commands. That approach was considered and rejected in favor of the layer-by-layer order above. The reasons:

- Per-layer focus is cleaner and less context-switchy than bouncing between convention, skill, and command authoring.
- Writing each layer as a coherent set produces stronger internal consistency (the 5 conventions naturally feel like a family when written together; same for the 15 skills).
- The conventions and templates layers are essentially zero-risk because they're pure spec — build them in full and cash in the cohesion benefit immediately.

The tradeoff being accepted: if the convention → skill → command relationship has a structural flaw, it surfaces after writing 4 conventions + 3 templates + 15 skills + 2 subagents rather than after one of each. Mitigations: most of these files are short and well-specified by this document, the structural risk is real but bounded, and refactoring skills when the first command lands is a tolerable cost.

If the first command lands and reveals a shape change, expect to revisit some skills. Treat that as expected, not as a failure.

### Within-layer ordering hints

Inside each layer, dependency order still matters for a few specific items:

- **Conventions**: `frontmatter-schema.md` before `task-format.md` and `epic-format.md` (they reference it). The companion `docs/metis-write-rules.md` is written last (it encodes cross-file rules that depend on understanding the other formats and the layer split).
- **Templates**: Any order; they're peers.
- **Skills**: `reconciling-docs` is the heaviest skill; budget accordingly. The decomposing/writing pairs (`decomposing-work-into-tasks` + `writing-a-task-file`; `decomposing-build-into-epics` + `writing-an-epic-file`) are independent siblings — either order within a pair is fine, and the two halves are loaded separately by callers that only need one.
- **Subagents**: Any order; they're peers once the skills they reference exist.
- **Commands**: `/metis:init` last (scaffolds everything). Otherwise any order, though grouping by workflow phase (setup → planning → feature loop → sessions → change management → epic boundaries → maintenance) is a sensible default.

---

## What's deferred to v0.2+

Explicitly out of scope for v0.1, to keep the shipping bar reasonable.

- **`/metis:explore`** and a dedicated `docs/SYSTEM.md` or `docs/ARCHITECTURE.md` artifact for existing-codebase synthesis. v0.1 handles existing codebases via prompt-seeded `/metis:build-spec` and agent-on-demand exploration.
- **`/metis:architect-pass`** — fresh-context architectural review at epic boundaries. Valuable but not critical for v0.1.
- **Cross-harness support** (Codex, OpenCode, Cursor, etc.). v0.1 is Claude Code only.
- **Plugin marketplace distribution.** v0.1 is clone-and-run.
- **A dedicated `doc-reconciler` subagent** for very large doc sets. v0.1 uses main agent + ad hoc subagents for compression.
- **Additional skills** like `writing-code-well`, `test-discipline`. v0.1 trusts the agent's defaults for these. Add when real usage reveals inconsistency.
- **`/metis:uninstall`** command. v0.1 users can manually delete per the MANIFEST.
- **Web dashboard, analytics, telemetry.** None in v0.1.

These aren't rejected — they're deferred. The rough order of v0.2 priorities would be: `/metis:explore` → `/metis:architect-pass` → cross-harness → everything else.

---

## Open questions

Things not fully decided. Worth addressing when building.

1. **Should `/metis:init` interactively ask questions, or take flags?** e.g. `/metis:init --name="MyProject"` vs. interactive Q&A. The mode question is gone (see Refinement 11), so the remaining init-time questions are lighter — project name, git-init-or-not, a few policy defaults. Leaning interactive for first-time users, with flags for power users.

2. ~~**How should `BOARD.md` be generated?**~~ **Resolved** during the audit pass: `BOARD.md` is dropped from v0.1. Nothing in the skill layer writes it, the *Current state* block of `scratch/CURRENT.md` already carries the triage view, and a staleness alarm on a file with no owner is noise. If drift between `CURRENT.md` and frontmatter later proves to be a real problem, reintroduce via a post-write hook backed by `.metis/scripts/refresh-board.sh` — no skill needed.

3. **Where exactly do plans live during `/metis:plan-task` → `/metis:implement-task`?** Current assumption: `scratch/plans/<id>.md`, gitignored. Confirm this is right.

4. **Should `/metis:feature` produce a feature spec file, or inline the feature description into task files?** ~~Probably a spec file at `features/NNN-<name>.md` when the project has a flat `tasks/` layout, and a new epic when the project uses `epics/`.~~ **Resolved** during the audit pass: flat mode writes task files only — no feature-spec file. In epic mode, the feature becomes a new epic (that was always the plan). Flat mode exists to skip grouping ceremony; a per-feature spec file re-imports it. If flat grows into needing grouping, `/metis:promote-to-epics` graduates the layout. See also #8.

5. **How to handle `/metis:generate-tasks` regeneration?** ~~If tasks exist already and user runs it again (e.g., after editing BUILD.md), does it refuse, merge, or replace?~~ **Partially resolved** by the post-handoff refinements: `/metis:sync` now handles the "spec changed, cascade to tasks" case explicitly, so `/metis:generate-tasks` can simply refuse regeneration and point users to `/metis:sync` for edits or `/metis:feature` for additions.

6. **What about task revision?** ~~If a task is half-done and the spec changes, how does Metis handle it?~~ **Resolved** by `/metis:sync`. Cascade rules by status: `done` tasks don't update in place (changes become new tasks or superseding decisions); `pending` / `in-review` can be edited in place; `in-progress` requires explicit confirmation.

7. **Should there be a `/metis:status` command?** Just a quick "where are we, what's blocked, what's the next thing" overview. Might be subsumed by `/metis:session-start`. Undefined.

8. **The name "features/"** directory (under a flat `tasks/` layout) vs. tagging tasks with `feature: NNN-<name>` frontmatter. ~~Tagging feels cleaner (keeps the structure flat) but features being first-class files makes them easier to find. Unresolved.~~ **Resolved** during the audit pass: neither. Flat mode has no grouping of any kind — task files land directly in `tasks/` with no `features/` directory and no `feature:` frontmatter tag. The argument for keeping flat flat won: if grouping becomes valuable, that's the signal to run `/metis:promote-to-epics`. See also #4.

9. **Token estimation for `/metis:reconcile` decision.** Should Metis automatically count tokens and choose between main-agent and hybrid modes, or should it prompt the user? Probably the former, with a manual override flag.

10. **Subagent output persistence.** When a subagent returns its summary, where does it go? Inline in the parent's chat? Appended to the task file? Both? Spec this out when building.

11. **Is `/metis:sync` aggressive or explicit?** Should it auto-detect drift at every `/metis:session-start`, or only run when the user explicitly invokes it? Leaning explicit (ambient alerts are fatiguing), with a light session-start banner like "looks like `docs/` changed since last session, want to run `/metis:rebaseline`?"

12. **Does `/metis:log-work` require task names, or infer them from the diff?** Inference is nicer ergonomically but can go wrong quietly. Leaning "name the tasks, agent verifies against diff."

13. **Are the names `/metis:sync` and `/metis:log-work` final?** `/metis:sync` is a bit generic; alternatives: `/metis:propagate-changes`, `/metis:reconcile-drift`. `/metis:log-work` alternatives: `/metis:record-work`, `/metis:catch-up`.

14. **Does the optional-prompt convention apply to every command, or only substantive ones?** Leaning "every command where the agent does real thinking" — excludes mechanical ones like `/metis:pick-task`, `/metis:session-start`. Also fine to say "all commands accept an optional prompt; most of them just ignore it if it doesn't apply."

---

## How to pick up from here

If you're a new Claude conversation reading this to continue the work:

**Where to start**: Layer by layer, per §14. Build all 4 conventions first, then all 3 templates, then all 15 teaching-register skills (with examples), then all 2 subagents, then all 22 command-register SKILL.md files (with `/metis:init` last). Propose a concrete plan for the current layer before writing, and surface any ambiguity against the doc as you go. If picking up at or after the commands layer, note that both registers live under `.claude/skills/metis/` — see Refinement 12 and the layout in §Directory structure.

**What to reference**:

- This document as the canonical source of design decisions.
- [Claude Code docs on skills](https://code.claude.com/docs/en/skills) for SKILL.md file format (both command-register and teaching-register skills use this).
- [Claude Code docs on subagents](https://code.claude.com/docs/en/sub-agents) for the agent file format.
- `.claude/commands/*.md` is still accepted by Claude Code but unused by Metis as of Refinement 12; the classic commands format docs at [slash-commands](https://code.claude.com/docs/en/commands) are informational only.

**What NOT to do**:

- Don't re-open the positioning questions unless you have new information. The five principles are set.
- Don't add more commands to v0.1 than the 22 listed. Scope creep kills v0.1.
- Don't try to build cross-harness support yet. Claude Code only.
- Don't implement `/metis:explore` yet. It's v0.2.
- Don't implement a lite mode. Metis is the heavy option.

**What to focus on**:

- Completing the current layer cleanly before starting the next.
- Dogfooding Metis on one real project after v0.1 is built. This is the only real validation.
- Writing out examples in each skill directory. Examples make skills concrete.
- Keeping command files thin. If a command is >1000 words, its skill isn't pulling its weight.

**How to handle disagreement**:

If something in this document seems wrong as you build, that's fine — the design isn't sacred. But document the change explicitly (update this doc, or write a `decisions/` entry in the Metis project itself). Silent drift from the design is the failure mode.

**How to handle external-model reviews**:

External-model reviews (ChatGPT, Gemini, etc.) have been useful signal during build — they catch wording gaps and missing cases our own flow glossed over. Two calibration points from experience: accept precision gains cheaply (tighter wording, testable conditions, cases the skill didn't cover); decline scope creep. External models lean toward adding sections, sequencing lenses, and product-management overlays that sound senior but cross Metis's layer boundaries — commands own orchestration, skills own artifact-shaping, conventions own format. If a suggestion would move a concern across those layers or push a skill past its cap, it's wrong even when well-argued in isolation. Keep the signal, keep the layering.

**The final principle worth internalizing**:

Metis is an opinionated tool for a specific audience. Its value comes from its opinions. Don't make it generic. If a design choice feels like it's trying to please everyone, it's probably wrong.

---

## Refinements (post-handoff design conversation)

The sections above describe the v0.1 design as it stood at the close of the original design conversation (20 commands / 10 skills / 5 conventions / 3 subagents). A subsequent design pass surfaced two structural gaps and three behavioral refinements. Those changes have been folded into the canonical sections above; this section preserves the rationale so future readers can understand *why* — not just *what*.

The net manifest impact of refinements and subsequent drafting: **+2 commands, +5 skills, no new conventions, no new subagents.** Current manifest: 22 / 15 / 5 / 3.

### Refinement 1 — Change management as a first-class concern

The original v0.1 design was implicitly one-directional: docs flow into `BUILD.md`, into epics, into tasks. The only feedback mechanism was `/metis:feature` for net-new additions. That's not enough — three change-propagation cases need explicit handling:

- **Case A — User edits a doc in `docs/`.** Most common, most dangerous, because the drift is silent. The doc change invalidates the premise of any downstream artifact that referenced it (`BUILD.md`, epics, task files via `docs_refs`). Without a detection mechanism, nothing notices.
- **Case B — User edits `BUILD.md` directly.** They've rethought architecture or scope. Epics and tasks beneath it may now be wrong.
- **Case C — User edits an epic or task file directly.** Localized, but can still cascade (e.g., changing an epic's scope changes what tasks belong under it).

Resolution: keep `/metis:rebaseline` as the read-only detector with real teeth (compares against a baseline using git markers + frontmatter `doc_hash` / `spec_version`), and add **`/metis:sync`** as the write counterpart that walks proposed cascading updates one at a time. Every accepted change appends a `decisions/` entry. Never auto-applies.

`/metis:sync` is **main-agent work, not subagent work** — it's cross-document reasoning, same category as Phase 0 reconciliation. A subagent can't see the whole picture.

Sub-decisions that follow:

- Task files need `doc_hashes` and `spec_version` in frontmatter so drift can be detected per task without re-reading everything.
- The cascade needs termination rules. Ten tasks downstream of one doc change shouldn't all be walked interactively — batch "these five look like simple text updates, approve as a group?" vs. "these two look substantive, let's walk them one at a time."
- Tasks that are `done` don't update in place — changes either become new tasks or decision entries that supersede. `pending` / `in-review` can be edited directly. `in-progress` requires explicit confirmation because someone's actively working on it.

This refinement also retires open question #6 (task revision when spec changes) by giving it a command, and partially closes #5 (task regeneration).

### Refinement 2 — Logging work done outside Metis

Metis must never *require* the user to route through its commands. Users will write code by hand — bugfixes, refactors, spikes, hotfixes — and Metis's view of the project will silently diverge from reality unless it has a catch-up command.

**`/metis:log-work [task-ids] <description>`**:

```
/metis:log-work 0007,0009 "Refactored the webhook handler to use the
new event schema. Task 0007 is done. Task 0009 I split into two —
the retry logic was bigger than expected; created 0011 for it."
```

The agent then:

1. Runs `git diff` on the relevant branch to see what actually changed.
2. Updates task file statuses and appends Notes sections combining the user's description with what the diff shows.
3. If the user says "done," verifies acceptance criteria against the diff (lightweight `/metis:review-task` pass).
4. If the user says "I split / added / merged tasks," handles the task-file CRUD.
5. If the diff touches architecture-level concerns, prompts for a decision entry.
6. Reports back any mismatch between what the user described and what the diff shows.

The key property: **the user's natural-language description is the source of truth for intent; `git diff` is the source of truth for what happened.** The command reconciles them and asks if there's daylight between them.

With no task argument, `/metis:log-work` creates a retroactive task file in `done` state with the description and diff as context — keeps the ledger complete without forcing users to pre-plan work they ended up doing ad hoc.

### How `/metis:sync` and `/metis:log-work` interact

Both commands reconcile external changes against Metis state. The split:

- **`/metis:sync`** reconciles *spec* drift (what we intend to build has changed)
- **`/metis:log-work`** reconciles *implementation* drift (what we've actually built has diverged from what's logged)

They likely share a "drift report" helper inside `propagating-spec-changes` and `logging-external-work` skills, but as user-facing commands they are different workflows and should not be merged.

Why these are worth doing in v0.1 rather than deferring: the whole point of Metis is that it holds up on a real project. A framework that assumes specs are stable and all work flows through its commands will be trusted until week one and then distrusted forever.

### Refinement 3 — `/metis:reconcile` covers gray areas, not just contradictions

The original `/metis:reconcile` was scoped to contradictions only. But contradictions and gray areas are different categories of doc problem:

- A **contradiction** is two specified things disagreeing (doc A says X, doc B says Y) — forces a *choice*.
- A **gray area** is one thing underspecified (doc says X but doesn't specify Y, or uses a term in a way that could mean two things) — forces a *specification*.

Both must be closed before coding. They get separate output files because the framing differs: `CONTRADICTIONS.md` entries cite both sides of the disagreement; `QUESTIONS.md` entries cite the ambiguous passage and articulate what's unclear. The `reconciling-docs` skill teaches both detection patterns.

Phase 0's exit criterion is now "`CONTRADICTIONS.md` and `QUESTIONS.md` are both empty (or consciously deferred)" rather than just contradictions.

The follow-on rename: `/metis:walk-contradictions` → **`/metis:walk-open-items`**. More honest than stretching "contradictions" to cover ambiguity.

### Refinement 4 — Walk-open-items offers genuine alternatives, not just dumps items

For each item, the agent offers **1–2 suggested resolutions** plus a free-form user-input option. This turns Phase 0 from "user sits and explains every decision from scratch" into "user confirms or redirects the agent's read." It's also a forcing function: the agent must do real thinking rather than dumping items back at the user.

Per-item UX:

```
Item 3 of 12 (question): Session duration

docs/auth.md says sessions "persist across browser restarts"
but docs/security.md mentions "short-lived tokens."
Duration is unspecified.

Agent's read:
  A) 30-day refresh token + 15-min access token. This is the common
     pattern that satisfies both passages — persistent across restarts
     via refresh, short-lived at the access layer.
  B) 7-day session with sliding expiration. Simpler, single token,
     matches "persist across browser restarts" more literally but
     less consistent with "short-lived tokens."

Your options:
  [A] go with A
  [B] go with B
  [C] your own answer (type it)
  [S] skip / defer
  [Q] quit the walk (resume later)
```

Two discipline points the `reconciling-docs` skill must teach:

- The agent's suggestions need to be **genuine alternatives** (not one real option and a straw man).
- For genuinely unclear items, the agent must be allowed to say "I don't have a good read here, need your input" rather than inventing options.

Every resolution writes the chosen answer into the relevant source doc and appends a minimal pointer to `RESOLVED.md`. Phase 0 does not produce `decisions/` entries — the docs being finalized are themselves the project's architectural baseline, and decisions begin when changes against that locked baseline (via `/metis:sync` or `/metis:log-work`) need their own record. Skipped items stay in `QUESTIONS.md` / `CONTRADICTIONS.md` for a later pass — they don't disappear.

### Refinement 5 — Walk-open-items resume behavior

The state-on-disk principle handles resume cleanly: **the files themselves are the resume state**, no separate bookkeeping file needed.

Each item gets a small status header:

```markdown
## Q3: Session duration
Status: open
Added: 2026-04-18

docs/auth.md says sessions "persist across browser restarts"
but docs/security.md mentions "short-lived tokens."
Duration is unspecified.
```

Item statuses: `open` (default), `resolved` (moved to `RESOLVED.md`), `deferred` ("not now, but don't bug me about this for a while"), `stale` (referenced doc has changed since item was captured — needs re-consideration; detected via `doc_hash`).

Starting or resuming the walk:

```
/metis:walk-open-items

You have 12 open items remaining (3 contradictions, 9 questions).
4 were resolved in the previous session.

Continue from the next open item, or pick a different starting point?
  [C] continue from Q3
  [L] list all open items
  [N] pick by number
  [Q] quit
```

Three additional pieces:

- New items can appear between sessions. If the user runs `/metis:reconcile` again (because docs changed substantially), new items get appended with `Status: open` — they show up in the next walk naturally.
- The walk supports **non-sequential navigation**. Users often know the answer to item 8 but not item 3. After resolving an out-of-order item, the walk asks "continue to next open item, or pick another?" rather than forcing linearity.
- **Un-resolve** (rare, but possible): leave the `RESOLVED.md` entry alone and add a new open item to the relevant active file that references the superseded decision. Resolution history is preserved; the superseding decision gets its own entry. Same pattern as ADR superseding.

### Refinement 6 — RESOLVED.md archive (don't re-read resolved items)

When the walk resolves an item, the entry is removed from the active file and appended to `docs/RESOLVED.md` as a minimal pointer:

```markdown
## Q3: Session duration
Resolved: 2026-04-19
Summary: 30-day refresh + 15-min access token.
```

The resolution's substance lives in the updated source doc — the doc itself is what downstream work reads as the architectural baseline, and the pointer is just a thin archive trail ("what did Phase 0 resolve?") at almost no bytes of load. No `decisions/` file is written for a Phase 0 resolution; decisions are reserved for changes against the baseline once development has started.

**Active files (read during walk):** `CONTRADICTIONS.md` and `QUESTIONS.md` — open and deferred items only.

**`RESOLVED.md` is never read during a walk** unless the user specifically asks. This is the load-bearing property: on resume, the agent's context is just the still-open items + `CLAUDE.md` + referenced doc sections. Resolved items are archival, not contextual.

Deferred items stay in the active files (still "open" from the walk's perspective). Stale items also stay in the active files (need re-consideration). One unified `RESOLVED.md` rather than separate files for contradictions and questions — by the time they're resolved, the distinction doesn't matter much.

This pattern generalizes: anywhere Metis accumulates items-to-work-through (future commands, future queues), resolved items should move to a separate "resolved" file so active work stays lean in context.

### Refinement 7 — Optional invocation prompts as a framework-wide convention

This was originally floated for `/metis:plan-task`, `/metis:implement-task`, `/metis:review-task`, then generalized. Every substantive Metis command accepts an optional free-text prompt that augments its default behavior:

```
/metis:plan-task 0007 "focus on retry semantics; the existing code uses tenacity, follow that pattern"
/metis:implement-task 0007 "skip mocking the webhook endpoint — use a real local test server"
/metis:review-task 0007 "pay close attention to the idempotency logic"
/metis:reconcile "give special weight to docs/billing.md, it's the most recent"
/metis:epic-breakdown "prefer vertical slices over horizontal layers"
/metis:sync "only propagate the auth doc changes, defer the billing ones"
/metis:epic-retro 001-auth "focus on the estimation misses"
```

The reasoning ties to principle #1 ("structure the project, not the agent"). If Metis forbids the user from giving in-the-moment guidance, then Metis *is* the religion you're trying to avoid. The framework provides scaffolding and opinions; it should not dictate how every task is approached.

Four discipline points (codified in `docs/metis-write-rules.md` and the subagent system prompts):

1. **Augment, don't replace.** The prompt augments the task file (or command context); it does not override it. If the prompt genuinely contradicts the task file, flag the conflict and ask.
2. **Flag scope expansion.** If the prompt expands scope, note it in the return rather than silently doing it.
3. **Acknowledge use explicitly.** The return states how the prompt was used. Traceable after the fact.
4. **Resolve named skills.** The prompt may name additional skills — Metis's own, user-authored, or project-specific; local or global — that the agent should consult alongside the skills the command already invokes. Resolve each reference the same way any skill reference is resolved, across whatever skill sources the runtime exposes. Invoked skills are acknowledged in the return; unresolvable names are flagged rather than guessed. User-referenced skills augment; they do not override the task file or the command's built-in skills.

The prompt is **ephemeral** — never persisted to disk.

The fourth rule is a later extension of the convention. The motivation: a user mid-project will accumulate skills that aren't part of Metis — team-review checklists, testing patterns, code-style documents, or personal skills kept in `~/.claude/skills/` — and being able to name them in the prompt is the natural way to bring them to bear on one specific invocation without wiring them into a command permanently. The alternative (editing the subagent's `skills:` frontmatter or bulk-loading project skills) fights the context-budget discipline and takes the "Metis is optional" principle in the wrong direction. Deliberately, the rule does not prescribe a lookup mechanism — the runtime already knows how to resolve skills across project-local, user-global, plugin, and Metis sources, and pinning the convention to one specific glob pattern would have missed skill sources that aren't in the project tree.

Open question (#14 above): does this convention apply to *every* command, or only substantive ones? Leaning "every command where the agent does real thinking" — excludes purely mechanical ones like `/metis:pick-task`, `/metis:session-start`.

### Refinement 8 — Reframing Metis as a context-maintenance toolset

The design to this point was described in workflow language — "the workflow Metis encodes," phases, a per-task feature loop — which made Metis sound like a pipeline the user has to route through. A later review reframed this. The point of Metis is not that the user runs `/metis:plan-task` → `/metis:implement-task` → `/metis:review-task` in order. The point is that at any moment, a fresh agent session can read on-disk state and know the project's intent, status, and history. How code actually got written between sessions is orthogonal.

Concretely:

- **The engineering-loop commands are optional.** The user can code alone, pair with an agent outside Metis, or drive work through Metis — and mix freely. Metis doesn't gate any of this.
- **Every artifact is user-editable.** Task files, epics, `BUILD.md`, `CURRENT.md`, and `docs/` are all fair game for hand editing. Metis's reconciliation commands (`/metis:sync`, `/metis:log-work`) absorb external edits rather than forbidding them.
- **Immutability claims were too strong.** Earlier drafts said task `id` and `title` were immutable; softened to "stable by default — if they change, reconcile via `/metis:log-work` or a resync." Same logic for the "10–30 tasks per epic" rule, which was dropped.
- **The conventions layer is a human/design-time reference.** At runtime, each skill / subagent / command carries only the slice it needs. Conventions files are not bulk-loaded into sessions.
- **Context efficiency is promoted to a load-bearing principle.** Metis should cost less context than the disorder it prevents. "Works but bloated" is a bug.

No manifest changes. The shift is in *framing and discipline*, which is carried through the principles in §4, the workflow section, the conventions descriptions, and the subagent load lists (parent `EPIC.md` added when the task lives under one).

### Refinement 9 — `reconciling-docs` split; Phase 0 does not write decisions

The original `reconciling-docs` skill covered both halves of the Phase 0 reconcile loop — detecting contradictions and gray areas, and walking one captured item through to resolution. As the loop hardened, the two halves pulled apart in scope and in caller: detection is batch work dispatched by `/metis:reconcile`, walking is one-at-a-time work dispatched by `/metis:walk-open-items`, and combining them in one skill meant each caller loaded content it didn't need.

Resolution: split the skill. `reconciling-docs` narrows to detection, surfacing, and stale detection during re-reconcile. A new `walking-open-items` skill owns per-item judgment (two genuine alternatives / one recommendation / an honest ask), the user-in-loop threshold for architectural vs. local resolutions, source-doc update, minimal `docs/RESOLVED.md` pointer shape, and status-lifecycle discipline (`open` / `deferred` / `resolved` / `stale`).

This refinement also committed to a sharper line between doc-finalization and decision-tracking: **Phase 0 walks do not write decisions.** The docs being finalized are the project's architectural baseline going into development; decisions begin at Phase 1, where changes against that locked baseline need their own record. Decision-writing authorship was tightened in `writing-decisions/SKILL.md` and `decision-format.md` to exclude `/metis:walk-open-items`. The single artifact a Phase 0 walk produces is a doc edit plus a minimal `docs/RESOLVED.md` pointer.

Net manifest impact: +1 skill.

### Refinement 10 — Implementation runs in the main session; `task-implementer` subagent retired

The original design placed all three task-level commands in the subagent layer: `task-planner`, `task-implementer`, `task-reviewer`. The implementer's tool restrictions (no writes to `BUILD.md`, `BOARD.md`, `scratch/CURRENT.md`, `decisions/`, or other task files) were framed as structural enforcement of workflow properties — the agent literally could not drift because the tool permissions would not let it.

A later pass surfaced two problems with this framing, both of which pulled toward moving implementation back to the main session.

First, the structural-enforcement argument sits uneasily against principle #1, "structure the project, not the agent." Tool-restricting a subagent is structuring the agent. The workflow properties the restriction protects — no silent `BUILD.md` edits, no cross-task bleed, no unannounced decision writes — are already carried by (a) prompt discipline in the command itself, (b) the reconciliation commands (`/metis:sync`, `/metis:log-work`) absorbing drift after the fact, and (c) the write flows `BUILD.md` and `decisions/` have of their own. Belt-and-braces with tool restrictions reads as ceremony once the prompt-level rules and reconciliation are in place.

Second, the context-firewall argument — heavy task-level reads staying out of the main session — is asymmetric across the three commands. Planning and review are one-shot heavy reads that produce a single artifact and return a compressed summary; the firewall pays off cleanly because the main session grows by a summary instead of by the inputs. Implementation is different: the main session *wants* to know what actually happened, asks follow-ups that re-derive context, and benefits from the user being able to interject mid-work. A subagent's compressed return compresses away information the parent will re-load anyway, and the lack of interactivity forces ambiguity into either a guess or a round-trip flag.

Resolution: retire `task-implementer` as a subagent. `/metis:implement-task` becomes a main-session command. The discipline that lived in the subagent's system prompt — load list (task file, parent `EPIC.md` when the task lives under one, approved plan at `scratch/plans/<id>.md` if present, only the docs in `docs_refs`), write scope (the assigned task file and the code it touches, nothing else), invocation-prompt rules (augment / flag scope expansion / acknowledge use), scope report per `honest-scope-reporting` on close — is carried by the command prompt instead. The same rules land in the same place; what changes is where the execution runs and whether the parent session watches it happen.

`task-planner` and `task-reviewer` stay as subagents. The planner is a legitimate one-shot heavy read (load context, produce plan file, return summary) where the context firewall pays off. The reviewer's case is stronger still: review independence is load-bearing — a reviewer that had seen the implementer's reasoning is not a reviewer — and fresh context is how the framework earns that independence. Tool restrictions on both stay valuable for the same reason they always were: the planner cannot start coding, the reviewer cannot "helpfully fix" and become a second implementer.

Two-stage review is preserved but its shape changes slightly: it is now main-session implementation followed by a fresh-context reviewer subagent. The independence the two-stage pattern is built around comes from the reviewer's freshness, not from the implementer being a subagent.

Net manifest impact: −1 subagent (3 → 2).

### Refinement 11 — "Mode" drops; project shape is emergent from the filesystem

The original design treated flat vs. epic as a configured mode: `/metis:init` asked the question, `.metis/config.yaml` carried a `mode:` field, and every command that behaved differently in the two shapes checked the config. A later pass identified this as ceremony against principle #2 (Metis is optional; it reconciles, it does not enforce).

The concept bought very little: a single source for layout checks, and a commitment point when the user graduated from flat to epic. Both are available from the filesystem directly. A project with an `epics/` directory containing at least one `EPIC.md` has an epic layout; a project with a flat `tasks/` directory has a flat layout. `/metis:promote-to-epics` is itself the graduation commitment — the config write would only have been bookkeeping after the fact.

Against those marginal wins, mode cost: an extra concept for users to learn before doing anything useful; a config file that must stay in sync with the filesystem (a drift source Metis would have needed to defend against); an init-time decision before the user knew which shape they wanted; and a collision with the "absorb user edits" principle — if a user hand-creates `epics/`, the framework should understand it, not check against a config that has started lying.

Resolution: drop `mode` as a first-class concept. Commands check the filesystem directly for the shape they need, and error messages name what's on disk rather than what's in a config:

```
This command requires an epics/ directory, but this project has a 
flat tasks/ directory at the root.
```

Specific adjustments folded into the canonical sections above:

- §Project modes: flat vs epic → **§Flat and epic layouts**. Reframed as structural state, not configured state.
- `/metis:init` no longer asks a mode question; it scaffolds the shared framework surface (`.metis/`, `.claude/`, `scratch/`, `CLAUDE.md` delimiters, `.gitignore` delimiters) and leaves the layout to whichever of `/metis:generate-tasks` or `/metis:epic-breakdown` the user runs first.
- `/metis:generate-tasks` infers layout from the filesystem: no argument when `tasks/` is flat, an epic-name argument when `epics/` exists. Errors on shape mismatch.
- `/metis:epic-breakdown`, `/metis:epic-retro`, `/metis:promote-to-epics` check for the specific filesystem preconditions they need and point at the likely-correct alternative when they fail.
- Frontmatter `epic` is **derived from path**: required when a task sits at `epics/<name>/tasks/<id>-*.md`, forbidden when it sits at `tasks/<id>-*.md`. The field is a consistency check against the filesystem, not a flag.
- Skills and subagents that previously said "in epic mode" now say "when the task lives under an epic" — the same load condition, stated in terms of the artifact's location rather than a global project flag.
- Ambiguous state (`tasks/` and `epics/` both populated) is surfaced by the next command that hits it, not silently resolved. Recovery is user-driven.

`.metis/config.yaml` may still exist for genuine configuration (`spec_version`, project name, defaults) but no longer carries a `mode:` field.

Net manifest impact: no file changes. The shift is in framing, command-level behavior, and the loss of one config field.

### Refinement 12 — Commands merge into SKILL.md format; `.claude/commands/` retires from Metis

Claude Code now treats `.claude/commands/<name>.md` and `.claude/skills/<name>/SKILL.md` as equivalent sources for the slash command `/<name>`. The skills format additionally supports a supporting-files directory, `disable-model-invocation`, `allowed-tools`, and the rest of the SKILL.md frontmatter surface; the commands format is parity-minus. The commands-layer build that had just completed used the classic `.claude/commands/metis/*.md` format. A review pass raised the question: given the format equivalence, is the two-directory split buying anything, or is it ceremony the new surface has made redundant?

The answer turned on separating two things that had been conflated. The *file format* difference between `.claude/commands/*.md` and `.claude/skills/<name>/SKILL.md` is real but thin — same invocation, same argument handling, same in-context loading. The *content register* difference between command-register content (orchestration — preconditions, load lists, write scope, subagent dispatch, return shape) and teaching-register content (artifact shape — what makes a good task file, when to split) is load-bearing and independent of file format. The layer discipline Metis earns — "commands own the turn, skills own the artifact" — is a property of content, not of directory.

Resolution: migrate all 22 commands to SKILL.md format, preserve the content-register split. Both layers now live under `.claude/skills/metis/`, distinguished by:

- **Directory prefix.** Command-register skills sit at `.claude/skills/metis/metis-<name>/SKILL.md` (e.g. `metis-plan-task/`, `metis-reconcile/`); teaching-register skills sit at `.claude/skills/metis/<skill-name>/SKILL.md` with no prefix (e.g. `planning-a-task/`, `reconciling-docs/`). The prefix is a filesystem-readable hint to the content distinction — an alphabetized listing of the directory surfaces the 22 top-level commands as a contiguous block. It does not affect slash-command resolution, which goes through the `name:` frontmatter.
- **Frontmatter.** Command-register skills carry `name: metis:<name>` (so `/metis:plan-task` resolves), `disable-model-invocation: true` (the user is the one invoking via the slash form; Claude does not autonomously trigger), and a short `description:`. Teaching-register skills carry a bare `name:` (e.g., `name: planning-a-task`) and `disable-model-invocation: true` (they are dispatched by commands, not ambient helpers).
- **Content shape.** Command-register files carry `## Preconditions`, `## Load`, `## Do not load`, `## Write scope`, `## Return` — the "own the turn" sections. Teaching-register files carry `## Read first`, `## Artifact shape`, `## Examples` — the "own the artifact" sections. The section names themselves signal which register a file is in.
- **Skill references.** Command-register files invoke teaching skills by reference ("Invoke by reference — read the skill file itself, do not paraphrase from memory: `planning-a-task`"). Teaching files do not reference other skills.

Three sub-decisions that followed from the migration:

- **Invocation-prompt rules live in one runtime-shipped place.** The four-rule block (augment / flag scope expansion / acknowledge use / resolve named skills) had accreted into fifteen commands plus both subagents — seventeen copies of the same paragraph. An initial pass on the migration put the canonical source in `docs/metis-write-rules.md`, but `docs/` is development-only and runtime artifacts must not reach into it; the second pass relocated the rules into `.metis/conventions/command-prompts.md`, which ships with every Metis install. Each command carries one command-specific example, one pointer at the convention file, and one command-specific "what not to persist it into" line. The subagents follow the same pattern. This resolved the largest source of genuine cross-file duplication the command layer had, and also surfaced a rule worth making explicit: **no runtime artifact (skill, subagent, template, convention) may reference `docs/`** — those files are design-time reading, and Metis is shipped as the `template/` tree without them.
- **`argument-hint` is dropped.** The classic commands-format frontmatter field does not appear in SKILL.md's documented schema. Argument shape now lives in the body under `## Arguments`, which most commands already had.
- **`.claude/commands/` is accepted but unused by Metis.** Claude Code continues to support that directory; Metis writes nothing there. The MANIFEST.md stops listing it.

What did not change: the subagents (`task-planner` and `task-reviewer`) still live at `.claude/agents/metis/*.md` in Claude Code's subagent format — that format has its own features (tool restrictions, color, the `name:` for dispatch) that SKILL.md doesn't carry. The teaching skills keep their existing locations and frontmatter. The command-to-skill-to-subagent mapping table above holds; only the *file paths of the commands* shifted.

The move also fixed one drift in the mapping: `/metis:implement-task` had listed `writing-a-task-file` as a skill reference for "the shape of an implementer's Notes append on close," but that skill teaches creating a new task file and is silent on appends. The migrated `/metis:implement-task` drops the reference and carries the Notes-append guidance inline — a short paragraph saying what the implementer writes is not worth a dedicated skill in v0.1.

Net manifest impact: conventions go from 4 to 5 (adding `.metis/conventions/command-prompts.md` — the canonical home for the four invocation-prompt rules, so runtime artifacts do not reach into `docs/`). Teaching skills and subagents unchanged. 22 command files move from `.claude/commands/metis/*.md` to `.claude/skills/metis/metis-<name>/SKILL.md`. One old skill reference fixed.

### Refinement 13 — Research as an internal capability, not a primary command

The build-spec, plan-task, and walk-open-items flows routinely encounter technical gaps the user's docs do not cover — what library handles a use case, what algorithm class fits, what the standard pattern is for an integration. Without a way to fill those gaps in-loop, three things happen: the agent stalls and asks the user for a technical call they may not know how to make; the agent guesses, producing a brittle commitment; or the brief / plan / question gets vague enough to defer the call ("auth: TBD"). None of those preserve the docs-first property — that the on-disk artifacts stay legible across sessions.

Resolution: research becomes a capability the relevant skills dispatch automatically when needed, not a primary command the user invokes.

The shape:

- **`domain-researcher` subagent.** Heavy web research happens in fresh context with restricted tools (`WebSearch`, `WebFetch`, read-only project access, write restricted to `docs/research/`). Returns a research note with options, tradeoffs, and a recommendation tagged with confidence (high / medium / low).
- **`doing-domain-research` teaching skill.** The universal *how* — scoping a question into sub-questions, source-quality hierarchy, citation discipline, confidence calibration, the 60-day staleness rule, the nine-section note shape. Read by the subagent.
- **Three integration points.** Each carries the *when* in its own teaching skill; the action layer just dispatches.

| Action layer | Teaching (carries the *when*) | Dispatches |
|---|---|---|
| `/metis:walk-open-items` (command skill) | `walking-open-items` | `domain-researcher` (for questions with factual answers the corpus does not settle) |
| `/metis:build-spec` (command skill) | `writing-build-spec` | `domain-researcher` (for technical commitments the corpus is silent on) |
| `task-planner` (subagent) | `planning-a-task` | `domain-researcher` (for plan-step commitments the task and source docs do not cover) |

- **Storage in `docs/research/`, not `scratch/`.** Research becomes first-class source material rather than ephemeral scratch. The trade-off: research notes are subject to the same drift detection as other docs (a note that changes triggers `/metis:sync` cascade if cited downstream), and they survive `scratch/` cleanup unconditionally. `walk-open-items` writes here when resolving a researchable question; the resolution cites the note in `docs/QUESTIONS.md` / `docs/RESOLVED.md`. `build-spec` cites it inline in the relevant `BUILD.md` section. `task-planner` cites it inline at the plan step.
- **No user gate.** The dispatching skill decides whether a question is research-worthy and dispatches automatically. Surfacing a gap as "ask the user" is reserved for things research cannot resolve — preference calls, business constraints, value judgments. A factual gap that the open web can settle is the dispatcher's job to settle.
- **Layering discipline.** In each chain, the *teaching skill* owns the research-mechanism content (when to dispatch, what to cite, staleness); the action layer (command skill or subagent) just dispatches per the teaching's guidance. This avoids duplicating research rules across the chain.
- **`docs/research/INDEX.md`.** Lookup table for prior research, scaffolded by `/metis:init`. One line per note with date, slug, one-line question, and confidence. The dispatching skills check it before dispatching to avoid commissioning a note that already exists; a note older than 60 days flags as a refresh candidate.

What did not change: `domain-researcher` is the only subagent that dispatches no other subagents (`task-planner` adds the `Task` tool to its allowlist so it can dispatch `domain-researcher` mid-plan; `task-reviewer` does not dispatch and is unchanged). The drift-detection mechanics (`/metis:rebaseline`, `/metis:sync`, the `doc_hashes` / `spec_version` baseline fields) treat `docs/research/` notes the same as any other doc citation — research becomes part of the docs-first property rather than an exception to it.

The dropped alternative: an early sketch had `/metis:research` as a primary user-invokable command with a Scope-Investigate-Synthesize phase structure and a four-choice menu of follow-ups (cite as-is / file decision / promote / discard). That shape made the user the gate for every research run. The integration-point pattern keeps the gate inside the dispatching skill where the gap was identified, which removes the round-trip and matches the docs-first principle that the framework owns the corpus's completeness.

### Refinement 14 — Teaching skills become references; the secondary-skill layer drops

Refinements 1, 2, and 9 introduced "teaching-register skills" — artifact-shape teaching (writing-a-task-file, planning-a-task, etc.) treated as first-class skills alongside the command-register skills. Refinement 12 then unified the file format: both registers became SKILL.md files under `.claude/skills/metis/<name>/`, distinguished by the `metis-` directory prefix on the command-register set. The conceptual layering held; the on-disk format collapsed cleanly.

The breakage came at packaging time. When Metis is shipped as a Claude Code plugin (per the plugin restructure that preceded this refinement), Claude Code's plugin namespace prepends `metis:` to every skill in `.claude/skills/metis/`. The 16 teaching-register skills surfaced as `/metis:writing-build-spec`, `/metis:walking-open-items`, etc., in the user's slash-command autocomplete. They were invokable from the user's perspective but meaningless without their parent command's context — `disable-model-invocation: true` did not hide them. The framework had two registers of content, but the user-facing surface treated them all as commands.

Resolution: drop the teaching-register skill layer entirely. The artifact-shape content moves into reference markdown documents that the calling skill loads by file path; nothing user-facing changes about the primary command set.

The split:

- **Single-caller references (7)** — moved into the calling primary's `references/` subdirectory at `.claude/skills/metis/<primary>/references/<name>.md`. Locality: the reference lives next to the one skill that uses it.
- **Multi-caller references (7) + subagent-only references (2)** — moved to a plugin-root `references/<name>.md` directory that is not registered as skills.

Subagent-only references live at the plugin root rather than inside `agents/<name>/` because subagents are single-file `.md` format, not directory format — restructuring `agents/` would risk breaking Claude Code's subagent loader.

Caller updates: `metis:<teaching>` cross-references in 13 primary SKILL.md files and 3 subagent .md files swap for file-path references. The `## Skills` section header in each caller renames to `## Read first` since the section now lists reference docs, not invoked skills.

Path conventions:

- Per-primary, from skills/<primary>/SKILL.md: `references/<name>.md`
- Plugin-root, from skills/<primary>/SKILL.md: `../../references/<name>.md`
- Plugin-root, from agents/<name>.md: `../references/<name>.md`

What did not change: the SKILL.md format for the 21 primary skills; the subagent format; the `.metis/conventions/` layer; the invocation-prompt convention; tool restrictions on subagents; the docs-first principle; the drift-detection mechanics.

The dropped alternative: keeping the teaching skills as first-class but adding a Claude Code mechanism to hide them from slash-command autocomplete. No such mechanism is documented; `disable-model-invocation: true` only blocks the model from autonomously triggering, not the user-facing surface. Splitting at the file layer (skills vs. references) is the durable fix.

Net manifest impact: skills drop from 38 (22 command-register + 16 teaching-register) to 21 (just the primary skills, after the various drops in Refinements 13–14). References (16 markdown docs) become a new layer in the Manifest table.

### Refinement 15 — Code exploration as an internal capability

The build-spec, generate-tasks, and plan-task flows routinely encounter a parallel gap to the one Refinement 13 addressed for the open web: when the project has an existing codebase, the calling skill needs to know what is in the source tree to make a commitment, and inline `Read` / `Glob` / `Grep` either over-reads (filling the calling skill's context with grep noise) or under-reads (forcing a commitment on vibes). The research subagent solved the open-web case; the same shape solves the code case.

Resolution: code exploration becomes a capability the relevant skills dispatch, parallel to research, with three intentional differences from `domain-researcher`.

The shape:

- **`code-explorer` subagent.** Read-only tools (`Read`, `Glob`, `Grep`); no `Write`, no web tools. Returns a compressed report inline as the tool result — answer, file:line evidence, seams, surprises, boundary. Nothing persists; the report is consumed in the same turn.
- **`exploring-code` reference.** Plugin-root reference (`references/exploring-code.md`) carrying the universal *how* — scoping the question, source order inside a repo, citation discipline (`path/to/file.py:42`), surprise-first synthesis, boundary discipline. Read by the subagent only. Calling skills carry the *when* in their own per-primary reference (see the integration-points table).
- **Three integration points.** Each carries the *when* in its own reference; the action layer just dispatches.

| Action layer | Reference (carries the *when*) | Dispatches |
|---|---|---|
| `/metis:build-spec` (skill) | `writing-build-spec` | `code-explorer` (eagerly, per architectural seam in existing-codebase mode) |
| `/metis:generate-tasks` (skill) | `decomposing-work-into-tasks` | `code-explorer` (per task whose surface is not fully named in the spec) |
| `task-planner` (subagent) | `planning-a-task` | `code-explorer` (sparingly, only when the task's surface is unfamiliar enough that planning would be guessing) |

Why the differences from `domain-researcher`:

- **No persistence.** Research findings are durable across sessions because external knowledge is reusable; code findings are tied to a specific commitment in a specific turn, and the underlying code changes. Persisting them creates stale artifacts. `code-explorer` writes nothing; the report returns inline and is cited where the calling skill commits (in `BUILD.md`, in a task's Context excerpt, in a plan step).
- **No INDEX.** Nothing to index; nothing to dedupe across sessions. A re-run is the right behavior — the code may have changed.
- **Aggressiveness controlled by the invoker, not the subagent.** The subagent always answers when dispatched; the dispatch policy lives in each calling skill's per-primary reference. Build-spec is eager, generate-tasks is per-task, task-planner is sparing. `exploring-code.md` carries the universal *how* (question-shape, citation discipline, report shape); the *when* lives with the caller.

What did not change: drift detection treats `BUILD.md`'s file:line citations the same as any other commitment — if the underlying code moves, `/metis:rebaseline` and `/metis:sync` catch the drift through the normal cascade. The docs-first property holds because nothing the code-explorer produces is durable; the durable artifacts (BUILD.md, tasks, plans) carry the cited refs and stand on their own.

The dropped alternative: persisting code-exploration reports to `docs/exploration/` parallel to `docs/research/`. The case for it was symmetry with research; the case against was that the artifacts go stale (research notes age more gracefully than code-shape descriptions), and the user already removed `scratch/exploration/` for the same reason — exploration that wants to live longer belongs in BUILD.md or a task file, not in its own directory.

### Manifest impact of all refinements

| Layer | Before refinements | After refinements |
|---|---|---|
| Skills (primary commands) | 20 | 21 (+`/metis:sync`, +`/metis:log-work`, renamed walk-contradictions → walk-open-items; later audit drops removed `/metis:scratch-cleanup` and `/metis:research`) |
| References | 0 | 17 (added in Refinement 14 from the dropped teaching-register layer: 7 per-primary + 9 plugin-root; Refinement 15 adds `references/exploring-code.md` at the plugin root) |
| Conventions | 5 | 5 (`frontmatter-schema` adds `doc_hashes` + `spec_version`; `write-rules` relocated to `docs/metis-write-rules.md`; `command-prompts.md` added in Refinement 12) |
| Subagents | 3 | 4 (Refinement 10 retires `task-implementer`, leaving `task-planner` and `task-reviewer`; Refinement 13 adds `domain-researcher`. `task-planner` gains the `Task` tool to dispatch `domain-researcher` and `code-explorer` mid-plan. Refinement 15 adds `code-explorer`.) |

Refinement 11 (mode removal) makes no change to the file counts above; its effect is on command-level behavior and the removal of the `mode:` field from `.metis/config.yaml`. Refinement 12 (commands merge into SKILL.md format) collapsed the commands-layer and teaching-skills-layer into one on-disk directory under `.claude/skills/metis/`. Refinement 13 (research as internal capability) added the `domain-researcher` subagent and the `doing-domain-research` reference (originally a teaching skill, demoted in Refinement 14), plus `docs/research/` as a new on-disk surface scaffolded by `/metis:init`. Refinement 14 (teaching skills become references) drops the teaching-register skill layer entirely; its 16 documents become reference markdown files (7 per-primary, 9 plugin-root). Refinement 15 (code exploration as internal capability) adds the `code-explorer` subagent and the `references/exploring-code.md` plugin-root reference; nothing on disk gets a new persistent surface.

---

## Appendix: the conversation that produced this

This document distills a long design conversation. Key moments worth knowing about, in case they help ground future discussions:

- The initial framing was "how do I go from a `docs/` directory to a working product with an agent." This grew into the four-phase workflow.
- Task files, task-scoped context, and subagent dispatch emerged as the solution to context management on large projects.
- The decision to build a framework (rather than adopt an existing one) came after evaluating Superpowers, gstack, and GSD and identifying a real gap: none of them take docs-first seriously.
- "Structure the project, not the agent" came late in the design — it's what differentiates Metis from existing rigid frameworks.
- The two-mode (flat/epic) design replaced an earlier plan for a single "medium/large" distinction.
- `.metis/` as a directory for framework scaffolding was chosen to keep project artifacts first-class at the root.
- Namespacing commands as `/metis:*` was a deliberate choice after recognizing collision risk with Claude Code built-ins.
- The v0.1 scope was repeatedly trimmed as features were added. Initial post-handoff scope was 20 commands / 10 skills / 5 conventions / 3 subagents. A subsequent design pass (see "Refinements" section) added two change-management commands (`/metis:sync`, `/metis:log-work`) and two supporting skills, bringing the manifest to 22 / 15 / 4 / 2 after all eleven refinements landed.
- Refinement 12, landing after the commands layer was first-drafted, collapsed the commands layer and teaching skills layer into one directory (`.claude/skills/metis/`) under the SKILL.md format while preserving the content-register split. The manifest file count stayed the same; what shifted was file paths, frontmatter, and the canonical home of the invocation-prompt rules.

The last meaningful decision before this handoff: Metis v0.1 manifest and the commands-merge-into-skills move. Ready to dogfood.
