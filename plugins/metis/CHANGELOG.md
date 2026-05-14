# Changelog

All notable changes to Metis are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/), versioning follows [SemVer](https://semver.org/).

## [0.4.0] — 2026-05-13

Plugin restructure. The on-disk layout is reorganized so each runtime installs only its own files: `.claude-code/` is the Claude install root (everything Claude needs at runtime lives there, the Claude marketplace's `source` field points at it), and `.codex/` is the Codex install root (generated from `.claude-code/` by `gen-metis-codex.py`, with a hand-maintained `.codex-plugin/` manifest sitting beside the generated trees). Claude users no longer carry the Codex `.codex/` tree as install baggage, and vice versa. Skills become fully self-contained: each skill folder holds its own `references/` with every script it runs and every markdown reference it reads, eliminating the plugin-level `.metis/` directory. Codex `AGENTS.md` is now driven by its own block body with runtime-appropriate `$metis-*` invocation syntax instead of sharing the `CLAUDE.md` block verbatim.

This is largely an internal refactor — the skill set, subagent set, and the `.metis/` artifacts inside the user's project are unchanged. The user-visible effects show up on the next `/metis-init` (or `$metis-init` on Codex): `CLAUDE.md` and `AGENTS.md` each get a runtime-appropriate Metis block, and both gain a new "Path conventions" section that explains how skill instructions resolve their path forms.

### Added

- `agents-block.md` — Codex-flavored sibling of `claude-block.md` that drives the `AGENTS.md` block. Uses `$metis-*` invocation syntax and describes path conventions appropriate to the Codex install. `init.sh` splices `claude-block.md` into `CLAUDE.md` and `agents-block.md` into `AGENTS.md` so the two files get the right body for each runtime.
- "Path conventions" section in both block bodies. Explains the path prefixes Metis skills use: `.metis/...` and `docs/...` (project root), `${CLAUDE_PLUGIN_ROOT}/...` (plugin install — Claude only), and bare paths like `references/foo.md` (skill folder).
- `.codex-plugin/plugin.json` — Codex's per-plugin manifest, hand-maintained by the plugin author. Lives inside `.codex/` next to the generated `skills/` and `agents/` trees. `gen-metis-codex.py` writes only those two generated subdirs and never touches `.codex-plugin/`.

### Changed

- Source-of-truth tree moves under `.claude-code/`. Everything Claude loads at runtime — skills, subagents, shared references, init data assets — lives there. The Claude marketplace's `source` field points directly at it, so a Claude install bundles only that subtree. The per-plugin Claude manifest moves to `.claude-code/.claude-plugin/plugin.json`.
- The plugin-level `.metis/` directory is gone. Scripts move into the `references/` folder of the skill that calls them:
    - `init.sh` plus its four data assets (`claude-block.md`, `agents-block.md`, `version`, `config.yaml.template`) → `skills/metis-init/references/`
    - `build-spec-preflight.sh` → `skills/metis-build-spec/references/`
    - `reconcile-preflight.sh` → `skills/metis-reconcile/references/`
    - `review-task-preflight.sh` → `skills/metis-review-task/references/`
    - `walk-open-items-preflight.sh` → `skills/metis-walk-open-items/references/`
- Two single-skill references move from the shared `references/` directory into the owning skill's local `references/`:
    - `planning-a-task.md` → `skills/metis-plan-task/references/`
    - `honest-scope-reporting.md` → `skills/metis-implement-task/references/`

  The shared `references/` directory now holds only references with genuine cross-referrer reach: `command-prompts.md` (every skill) and the three subagent-only references (`doing-domain-research.md`, `exploring-code.md`, `reviewing-against-criteria.md`).
- SKILL.md path forms simplify. Scripts are addressed as bare skill-local `references/foo.sh` (no `${CLAUDE_PLUGIN_ROOT}/.../*` prefix needed); only shared markdown references still use the `${CLAUDE_PLUGIN_ROOT}/references/X.md` form.
- `init.sh` consolidated. Was: dual-layout detection (Claude plugin tree vs. Codex skill copy, each with different relative paths to its data assets). Now: a single flat layout — all four data assets sit alongside `init.sh` in `metis-init`'s `references/` folder, same in both install trees.
- Codex SKILL.md output normalizes every reference path to ``this skill's `references/X` ``. Previously, paths derived from `${CLAUDE_PLUGIN_ROOT}/.../*` got the prefix while bare skill-local `references/X` paths were left unprefixed; the Codex tree mixed both conventions in the same document.
- Codex SKILL.md and agent TOML output translates Claude's `/metis-*` slash-command references into Codex's `$metis-*` form. Applies to SKILL.md bodies, the inlined reference content in agent TOMLs, and copied shared-reference markdown — Codex addresses skills with `$`, so leaving `/` in the generated artifacts would surface the wrong invocation syntax.
- `gen-metis-codex.py` substantially simplified. The script's output is bounded to `.codex/skills/` and `.codex/agents/`; `--check` comparison is similarly scoped, so the hand-maintained `.codex-plugin/` never triggers a stale flag. Removed: the `SCRIPTS_SRC` constant, the `METIS_INIT_ASSETS` constant and its post-loop planting step, the dual-extension `(scripts|references)/` alternation in the reference regex, and the `kind == "scripts"` branch in the reference copy loop. Net ~100 lines lighter.

### Fixed

- `gen-metis-codex.py` no longer creates an empty `references/` folder for skills with neither a local `references/` in source nor any shared-reference mentions in `SKILL.md`. Previously the destination folder was mkdir'd unconditionally during port; now it's only created when there's a shared reference to drop in.

[0.4.0]: https://github.com/gsaranti/pantheon/releases/tag/v0.4.0

## [0.3.0] — 2026-05-13

### Added
- Codex plugin support. Metis now installs and runs on both Claude Code
  and Codex. A new `scripts/gen-metis-codex.py` converts the canonical
  Claude tree to the Codex-shaped `.codex/` tree on demand.
- `init.sh` now splices the Metis block into both `CLAUDE.md` and
  `AGENTS.md`, keeping them independent files so runtime-specific
  instructions outside the markers are preserved.

### Changed
- Metis ships from the Pantheon marketplace at gsaranti/pantheon.
  Install commands:
    - Claude: `/plugin marketplace add gsaranti/pantheon` then
      `/plugin install metis@pantheon`
    - Codex: `codex plugin marketplace add gsaranti/pantheon`, then
      install from the `/plugins` UI
- `command-prompts.md` consolidated into `references/` from its prior
  location in `.metis/conventions/`.

[0.3.0]: https://github.com/gsaranti/pantheon/releases/tag/v0.3.0

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

[0.2.0]: https://github.com/gsaranti/pantheon/releases/tag/v0.2.0

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

[0.1.2]: https://github.com/gsaranti/pantheon/releases/tag/v0.1.2

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

[0.1.1]: https://github.com/gsaranti/pantheon/releases/tag/v0.1.1
[0.1.0]: https://github.com/gsaranti/pantheon/releases/tag/v0.1.0
