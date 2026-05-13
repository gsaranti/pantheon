# Changelog

All notable changes to Metis are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/), versioning follows [SemVer](https://semver.org/).

## [0.2.0] — 2026-05-12

Lean refactor. The runtime surface is trimmed substantially: 9 skills (was 21), 3 subagents (was 4), the on-disk state collapses to a handful of markdown files in one directory (was spread across `.metis/`, project root, `docs/`, `decisions/`, `tasks/` or `epics/`, `scratch/`). Slash commands move from `/metis:*` to `/metis-*` to avoid collision with built-in Claude Code commands.

This is a breaking change in nearly every dimension. There is no automatic migration from 0.1.x state — a 0.2.0 project starts fresh with `/metis-init`. The 0.1.x design documents are preserved in `deprecated/` for reference.

### Added

- `/metis-plan-task` takes a free-text task description rather than a task ID. The plan lives in chat by default; nothing is written to disk. Tip: run in plan mode (Shift+Tab) for Claude Code's native review UI.
- `/metis-implement-task` gains a "Knowing when to stop" redline: when the verification command fails repeatedly, the agent surfaces upstream rather than grinding on the loop. Three redline signals: (a) a fix would touch files outside the plan's expected file changes, (b) two consecutive attempts produce errors with the same root cause, (c) the fix risks breaking unrelated behavior.
- `/metis-walk-open-items` presents resolution choices with a lettered menu (`[A]` / `[B]` / `[C] type your own`) and unbounded thinking time — plain chat input, no `AskUserQuestion` timeout to worry about.
- Reconcile-time stub pre-creation: `/metis-reconcile`'s preflight creates `SYNTHESIS.md`, `INDEX.md`, `CONTRADICTIONS.md`, and `QUESTIONS.md` as stubs on first run, so Edit can target them on subsequent rereconciles rather than Write re-emitting unchanged content as output tokens.
- `metis-task-reviewer` receives a resolved `BASELINE` from `review-task-preflight.sh`, so the cascade (`main` → `master` → `origin/main` → `origin/master`) is determined in one place rather than re-derived by the subagent.

### Changed

- All slash commands renamed from `/metis:*` to `/metis-*`. The previous `/metis:init` collided with Claude Code's built-in `/init`; the new naming is unambiguous and Windows-filesystem-safe.
- All three surviving subagents prefixed: `metis-code-explorer`, `metis-domain-researcher`, `metis-task-reviewer`.
- `BUILD.md` moves from the project root into `.metis/BUILD.md`. All Metis state now lives in `.metis/`: `BUILD.md`, `CURRENT.md`, `SYNTHESIS.md`, `INDEX.md`, `CONTRADICTIONS.md`, `QUESTIONS.md`, `RESOLVED.md`, `config.yaml`. A single `rm -rf .metis/` removes everything Metis manages (plus a small delimited block in `CLAUDE.md`).
- `BUILD.md` opens with a synthesis-like entry (concise own-words explanation of what's being built) before the risk lead.
- `metis-domain-researcher` no longer writes a research note. Findings return inline; the parent applies them to the artifact that prompted the dispatch. The `docs/research/` directory and its `INDEX.md` are gone.
- Review verdicts drive manual user action (commit / merge / re-implement) rather than a task-file status transition — no task files means no status field to flip.
- Reconciliation skills (`/metis-reconcile`, `/metis-walk-open-items`) use Edit on re-runs to avoid re-emitting unchanged items as Write output. Specifically: INDEX, CONTRADICTIONS, QUESTIONS on rereconcile; per-item operations during walks.
- Open questions surfaced during a session live inline in `.metis/CURRENT.md`'s *Open questions* block. The separate `scratch/questions.md` file is gone. (`.metis/QUESTIONS.md` remains as the reconcile-owned docs-corpus gap file.)

### Removed

- 12 skills: `epic-breakdown`, `epic-retro`, `feature`, `generate-tasks`, `log-work`, `pick-task`, `promote-to-epics`, `pushback`, `rebaseline`, `scope-check`, `skeleton-plan`, `sync`. The framework no longer encodes a flat-vs-epic project layout, an explicit task backlog, or a decisions log.
- The `tasks/`, `epics/`, `decisions/`, and `scratch/` directories. No more task files, `EPIC.md`, decision entries, or `scratch/plans/<id>.md`.
- The `task-planner` subagent. Planning runs in the main session; the plan lives in chat, naturally available to the implementer.
- Frontmatter schema for tasks (`id`, `status`, `depends_on`, `touches`, `docs_refs`, `doc_hashes`, `spec_version`). No tasks means no frontmatter.
- 4 conventions: `task-format.md`, `epic-format.md`, `decision-format.md`, `frontmatter-schema.md`. Only `command-prompts.md` remains.
- 3 templates: `task.md`, `epic.md`, `decision.md`.
- 8 reference examples: `good-build-spec.md`, `good-plan.md`, `good-review.md`, `good-session-handoff.md`, `good-decision.md`, `good-decision-superseding.md`, `good-epic.md`, `good-task.md`. Textual guidance in references covers the shapes; examples added maintenance burden without clear value.
- `lib/common.sh` and all its helpers. Surviving preflights inline what they need.

### Notes

- Plans and scope reports live in chat by default — they're not artifacts. Token-cost rationale: writing a file emits the full content as output tokens (~5× input rate, uncached). When the implementer (same session) needs the plan, it's already in cache for input rates; when a future session needs it, `/metis-session-end` captures the relevant shape in `CURRENT.md`.
- The 0.1.x design history (`metis-write-rules.md`, the v0.1 handoff, the skills review) moves to `deprecated/` rather than being deleted. The directory name signals it's not current.

[0.2.0]: https://github.com/gsaranti/Metis/releases/tag/v0.2.0

## [0.1.2] — 2026-04-28

Hotfix release. Plugin-root references, conventions, templates, and examples didn't load under Claude Code's plugin distribution because `../../references/X.md`, `../references/X.md`, and `.metis/conventions/X.md` were resolving against the user's project (where they don't exist) instead of the plugin install.

### Fixed

- All plugin-side content paths in skills, subagents, and references now use `${CLAUDE_PLUGIN_ROOT}/...` so they resolve against the plugin install:
  - SKILL → reference loads
  - Subagent → reference loads
  - Reference → convention loads
  - Reference → template loads
  - Reference → example loads
- `init.sh` no longer copies conventions, templates, or references into the user's project — that content stays in the plugin install and is referenced by absolute path. The user's `.metis/` is now minimal: `config.yaml`, `version`, `MANIFEST.md`.

### Changed

- `walk-open-items` auto-land threshold tightened. The previous "agent lands local items" rule was generalizing too liberally to API contracts, validation behavior, and cache strategies. Default is now "ask"; auto-land is reserved for filling in a specific value within a shape the corpus has already committed to.
- `walk-open-items` SKILL gained an explicit "Pacing" section requiring per-item user input rather than chaining items together.

[0.1.2]: https://github.com/gsaranti/Metis/releases/tag/v0.1.2

## [0.1.1] — 2026-04-28

Hotfix release. v0.1.0 didn't actually work post-install; v0.1.1 does.

### Fixed

- Skill script paths now use `${CLAUDE_PLUGIN_ROOT}` so they resolve against the plugin install directory rather than the user's project. Affects all 14 skills that invoke a script.
- Preflight + utility scripts (13 of them) now use `${PWD}` as `PROJECT_ROOT` instead of computing it from `${SCRIPT_DIR}/../..` (which landed in the plugin install, not the user's project).
- `init.sh` rewritten for plugin distribution: reads templates/version from `PLUGIN_ROOT`, writes outputs to the user's project, copies `.metis/conventions/` and `.metis/templates/` into the project so skills can load them as project-relative paths.
- `.claude-plugin/plugin.json`: `author` field reshaped from a string to the documented `{ "name": ... }` object form.
- `.claude-plugin/marketplace.json`: added the documented-required top-level `owner` object; same `author` string → object fix in the embedded plugin entry.

## [0.1.0] — 2026-04-24

Initial release.

### Added

- 21 skills under `/metis:*` covering setup, doc reconciliation, build spec + backlog, the optional engineering loop, sessions, and reconciliation of work done outside Metis.
- 4 subagents (`task-planner`, `task-reviewer`, `domain-researcher`, `code-explorer`) with scoped tool restrictions.
- 17 references (10 plugin-root + 7 per-primary) carrying artifact-shape teaching.
- 5 conventions specifying canonical on-disk formats (`frontmatter-schema`, `task-format`, `epic-format`, `decision-format`, `command-prompts`).
- 14 bash scripts handling preflight checks, drift detection, and project init, with a shared `lib/common.sh` for cross-script helpers.
- Two project layouts: flat (`tasks/`) and epic (`epics/<name>/tasks/`), with `/metis:promote-to-epics` graduating one to the other.
- Drift detection via `doc_hashes` + `spec_version` baseline fields, surfaced by `/metis:rebaseline` and walked as a cascade by `/metis:sync`.
- `docs/research/` directory with INDEX-based prior-art lookup and a 60-day staleness window for the `domain-researcher` subagent.
- Four-phase canonical workflow (reconcile → build spec + backlog → skeleton → optional engineering loop), with the loop optional at every step.

### Notes

- v0.1 targets Claude Code; other harnesses are deferred.
- The engineering loop is one path; pair-programming with hand-edits + `/metis:log-work` reconciliation is equally supported.

[0.1.1]: https://github.com/gsaranti/Metis/releases/tag/v0.1.1
[0.1.0]: https://github.com/gsaranti/Metis/releases/tag/v0.1.0
