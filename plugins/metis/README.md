# Metis

> *Wisdom before code.*

A lightweight toolset for keeping a project's intent, status, and history legible across Claude Code sessions.

Metis structures the project, not the agent — it puts a small, predictable set of artifacts on disk so a fresh session can rehydrate cleanly, no matter how the work was done between sessions. The runtime surface is minimal: a handful of markdown files in one directory, nine slash commands, three subagents.

---

## Contents

- [What Metis is](#what-metis-is)
- [Who it's for](#who-its-for)
- [Installation](#installation)
- [The workflow](#the-workflow)
- [The skill set](#the-skill-set)
- [Subagents](#subagents)
- [Principles](#principles)
- [License & Repository](#license--repository)

---

## What Metis is

A filesystem layout, a set of skills, and three subagents — all designed so the next agent session can pick up cleanly from disk.

What you get on disk, all in `.metis/`:

- **`BUILD.md`** — the project's forward-looking architecture brief. Opens with a short synthesis of what's being built; commits to the riskiest architectural decision and names the first vertical slice.
- **`CURRENT.md`** — the session handoff. The first file every new session reads. Four blocks: what happened, current state, open questions, where to start.
- **`SYNTHESIS.md`** — own-words summary of the docs corpus (docs-first projects).
- **`INDEX.md`** — concept → source-doc map (docs-first projects).
- **`CONTRADICTIONS.md`** / **`QUESTIONS.md`** / **`RESOLVED.md`** — captured items from doc reconciliation, plus a thin pointer-archive of what's been resolved.
- **`config.yaml`** — project name and Metis version pin.

What you get as skills: nine slash commands under `/metis-*`. Three subagents (`metis-code-explorer`, `metis-domain-researcher`, `metis-task-reviewer`) provide fresh-context firewalls for heavy reads and independent judgment.

That's the whole runtime surface. No task files, no decisions log, no scratch directory, no epics, no flat-vs-epic project shape. Plans and implementation scope reports live in chat — `CURRENT.md` captures them across session boundaries when continuity matters.

---

## Who it's for

Engineers using Claude Code on projects where state needs to survive across sessions — typically projects that start with a pile of documentation (UX requirements, design docs, technical specs) and that multiple sessions will return to.

If the work is a throwaway prototype, a one-session script, or something you won't return to: **Metis is the wrong tool.** The structure pays off when sessions need to rehydrate; without that, it's overhead.

---

## Installation

Metis ships as a plugin for both Claude Code and Codex. Pick the section for your agent.

### Claude Code

```
/plugin marketplace add gsaranti/Metis
/plugin install metis@metis
```

### Codex

Register the Metis marketplace from your shell:

```bash
codex plugin marketplace add gsaranti/Metis
```

Then open Codex, browse to the `metis` marketplace in the plugin directory, and install Metis:

```
codex
/plugins
```

One additional one-time step: Codex doesn't yet support plugin-bundled subagents, so symlink Metis's three subagents into your user-scoped Codex agents directory:

```bash
mkdir -p ~/.codex/agents
for f in ~/.codex/plugins/cache/*/metis/*/.codex/agents/metis-*.toml; do
  [ -e "$f" ] && ln -sf "$f" ~/.codex/agents/"$(basename "$f")"
done
```

This makes `metis-code-explorer`, `metis-domain-researcher`, and `metis-task-reviewer` available across all your Codex projects. Re-run after plugin updates pick up any changes to the subagent definitions.

### Per-project setup

After installation (either runtime), run `/metis-init` once per project to scaffold project-specific files — `.metis/config.yaml`, the `.metis/CURRENT.md` stub, and a delimited block in both `CLAUDE.md` and `AGENTS.md`. Init is non-destructive — only the content between Metis's delimiters is touched, so each file can keep runtime-specific instructions outside the block.

After init, type `/metis-` to see the full skill set.

---

## The workflow

The canonical flow:

```
Setup            →   /metis-init
Docs reconcile   →   /metis-reconcile             (if docs/ exists)
                     /metis-walk-open-items       (resolve items into source docs)
Build spec       →   /metis-build-spec            (produces .metis/BUILD.md)
Per task         →   /metis-plan-task "<task>"    (plan in chat)
                     /metis-implement-task        (executes; closes with scope report)
                     /metis-review-task           (independent judgment)
Per session      →   /metis-session-start         (rehydrate)
                     ... work ...
                     /metis-session-end           (update CURRENT.md)
```

Two independent variations on the flow above:

- **No `docs/` corpus.** Skip `/metis-reconcile` and `/metis-walk-open-items`. Pass a description directly: `/metis-build-spec "<description>"`.
- **Existing codebase.** `/metis-build-spec` auto-dispatches `metis-code-explorer` per architectural seam to anchor the brief to the existing code; the brief becomes a delta describing what this build adds, changes, or replaces. This is independent of the docs question — you can have both `docs/` and existing code, in which case the brief is a docs-driven delta.

Plans and scope reports live in chat by default; only `CURRENT.md` persists session-to-session. `/metis-session-end` captures enough of an in-flight plan or scope report in `CURRENT.md` for the next session to resume cleanly.

---

## The skill set

Nine skills, all `/metis-*`:

### Setup

- **`/metis-init`** — scaffold `.metis/` and the `CLAUDE.md` block. Run once per project. Non-destructive.

### Docs reconcile (when `docs/` exists)

- **`/metis-reconcile`** — read the `docs/` corpus, produce `.metis/SYNTHESIS.md` (own-words summary), `.metis/INDEX.md` (concept → source-doc map), `.metis/CONTRADICTIONS.md` (direct conflicts), `.metis/QUESTIONS.md` (gray areas). Re-reconcile preserves prior items and uses Edit for unchanged content to avoid re-emitting it as output tokens.
- **`/metis-walk-open-items`** — walk through open items one at a time. Agent offers 1–2 alternatives, a recommendation, or asks. Lettered-menu UX (`[A]` / `[B]` / `[C] type your own`) with unbounded thinking time. Each resolution updates the source doc and appends a pointer to `.metis/RESOLVED.md`.

### Build spec

- **`/metis-build-spec`** — produce `.metis/BUILD.md` from the reconciled corpus, a prompt, or an existing codebase delta. Opens with a synthesis-like entry, leads with the riskiest architectural decision, names a first vertical slice.

### Per task

- **`/metis-plan-task "<description>"`** — draft an implementation plan from a free-text task description. Plan lives in chat (no file written). Tip: run in plan mode (Shift+Tab) for Claude Code's native review UI.
- **`/metis-implement-task`** — implement against the plan in context. Code + tests, with a verification command and a four-category scope report at close (Skipped / Deferred / Stubbed / Handled differently). Includes a "knowing when to stop" redline so a stuck verification loop surfaces upstream instead of grinding.
- **`/metis-review-task`** — dispatch `metis-task-reviewer` to judge the diff against the description, plan, and scope report. Returns `approve`, `approve-with-nits`, or `reject-with-reasons` with per-criterion evidence.

### Per session

- **`/metis-session-start`** — load `.metis/CURRENT.md` plus `BUILD.md` and `INDEX.md` if they exist. Orient the fresh session.
- **`/metis-session-end`** — rewrite `.metis/CURRENT.md` with the four-block handoff. Sized for the ~1k-token cap so rehydration stays cheap.

---

## Subagents

Three subagents, each with scoped tool restrictions that enforce workflow properties structurally:

- **`metis-code-explorer`** (Read / Glob / Grep) — investigate one question against the existing source tree. Returns a compressed inline report: answer, file:line evidence, seams, surprises, boundary. Auto-dispatched in existing-codebase mode by `/metis-build-spec`, and by `/metis-plan-task` for unfamiliar surfaces.
- **`metis-domain-researcher`** (Read / Glob / Grep / WebSearch / WebFetch) — investigate one technical question against the open web. Returns findings inline; no file written. Auto-dispatched by the skills that need a fact the corpus doesn't settle (`/metis-walk-open-items`, `/metis-build-spec`, `/metis-plan-task`).
- **`metis-task-reviewer`** (Read / Glob / Grep / Bash) — review one diff against the description, plan, and scope report it was meant to satisfy. Bash is read-only against git (`git diff`, `git status`, verification commands) — no mutating commands. Read-only against code; the reviewer reports findings rather than "helpfully fixing."

The pattern: heavy reads happen in fresh subagent context; the parent's context grows by the synthesized report, not by everything the agent read to make it.

---

## Principles

The load-bearing opinions. Everything else is convention.

1. **Structure the project, not the agent.** Metis provides artifacts and conventions. The agent decides how to solve each task. No TDD enforcement, no persona role-play, no prescribed reasoning steps.

2. **Optional at every step.** Every artifact Metis produces can be hand-edited at any time. The skills orchestrate; they don't enforce. You can drive work through the skills, pair with an agent without invoking any of them, or mix freely — Metis reads from disk and trusts what it finds there.

3. **Docs before code, when docs exist.** Reconciling first surfaces contradictions and gaps before they compound into drift. The strongest recommendation Metis makes — but a recommendation, not a gate.

4. **Token economy is load-bearing.** Plans and scope reports live in chat (no output-token cost for writing files; cached on subsequent turns). Subagents return summaries, not their full reads. Re-reconcile uses Edit for unchanged content rather than Write. Every artifact Metis writes is a deliberate choice with continuity value.

5. **Fresh instances at natural boundaries.** Resumption is for continuity within a thread of work. Starting a new phase (build-spec → per-task work, an unrelated feature) in a fresh Claude Code instance drops accumulated context that would otherwise compound. `CURRENT.md` carries enough across sessions to pick up; the rest stays in the conversation that produced it.

---

## License & Repository

**License**: MIT. See [`LICENSE`](LICENSE).

**Repository**: <https://github.com/gsaranti/Metis>
