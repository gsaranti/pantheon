# Write rules

A design-time reference. This file exists so the full who-writes-where picture is readable in one place. **It is not bulk-loaded at runtime.** Individual skills and subagent system prompts carry only the one or two rules they actually need. If this file is growing such that it has to be read in full during a task, one of the skills is underspecified.

File *structure* is covered in `task-format.md`, `epic-format.md`, `decision-format.md`, and `frontmatter-schema.md` (under `template/.metis/conventions/`). This file is about *behavior*.

## The underlying property

Metis's value is that a fresh agent can read on-disk state and know where the project stands. That only works if the state on disk is a reliable record. These rules exist to keep that property honest — they do not exist to prevent the user from editing their own files. The user can edit anything. The rules govern who *Metis's own agents and commands* write to.

## Layer responsibilities

Metis is built in three conceptual layers — skills, references, and conventions — with a strict one-way dependency: **skill → reference → convention**. Subagents are a variant of the skill layer. Each layer has a distinct kind of content; keeping them separate is what lets the framework scale without drift.

**File layout.** Skills are the user-invokable commands at `.claude/skills/metis/<name>/SKILL.md` with `name: <name>` in frontmatter (Claude Code's plugin namespace prepends `metis:`, so `/metis:plan-task` resolves against `.claude/skills/metis/plan-task/SKILL.md`). References are markdown documents skills load at runtime by file path; they are not first-class skills. Single-caller references live at `.claude/skills/metis/<primary>/references/<name>.md`; multi-caller and subagent-only references live at the plugin-root `references/<name>.md`. Subagents live at `.claude/agents/metis/<name>.md` in Claude Code's subagent format. See Refinement 14 in the handoff for the reasoning behind dropping the teaching-register skill layer.

**Skills own the turn.** A skill's SKILL.md is invocation-shaped orchestration — argument parsing, filesystem-state checks (does the project have an `epics/` directory? a flat `tasks/`? neither?), error messages on mismatch, the specific load list for this invocation, subagent dispatch if any, invocation-prompt handling, write scope and confirmation/preview flows, and the output format back to the user. The register is directive. Skills load references by file path rather than inlining their content.

**References own the artifact.** A reference is artifact-shaped teaching — what makes a good X, when to split, how sections should read, which conventions to consult. The register is descriptive. A reference names the *kinds* of inputs the artifact requires ("a body of work plus the source docs it references") but does not prescribe specific files, loading sequence, or session orchestration. References cite conventions; references do not reference other references; references do not carry routing metadata.

**Subagents are scoped skills.** A subagent's system prompt is the skill equivalent that runs in a fresh context window with restricted tools. Same layer, same rules: load references by path; name specific inputs and flow; do not teach artifact shape. Subagents live at `.claude/agents/metis/<name>.md`; their file format is the Claude Code subagent format, not SKILL.md.

**Conventions own the on-disk format.** Section order, filename rules, frontmatter schema. Conventions are static reference; they do not reach upward into skill or reference behavior.

**Path conventions for loading references:**

- From a skill at `skills/<primary>/SKILL.md` to its own per-primary reference: `references/<name>.md`
- From a skill at `skills/<primary>/SKILL.md` to a plugin-root reference: `../../references/<name>.md`
- From a subagent at `agents/<name>.md` to a plugin-root reference: `../references/<name>.md`

The one-way rule is what keeps the split honest: a reference that starts naming specific files is drifting into skill territory; a skill that starts teaching section structure is drifting into reference territory. When content fits none of the layers cleanly, it usually belongs inline in the skill — which is allowed to be directive about a specific turn.

## File-by-file write permissions

The rules below describe who among Metis's own agents and commands writes to each file. **The user may hand-edit any file at any time**; that is not called out in every entry because it is true everywhere. What each entry adds is the specific property (append-only, generated, delimited, etc.) that the user should know they are opting out of if they edit by hand.

### Project root

#### `BUILD.md`

- **Writes**: `/metis:build-spec` (initial creation), `/metis:sync` (propagating upstream doc changes).
- **Subagents**: never.
- **`/metis:implement-task`**: never. Implementation runs in the main session but treats `BUILD.md` as off-limits — if a task cannot be completed without a `BUILD.md` edit, the command surfaces the conflict rather than editing. Spec changes are `/metis:sync` territory.
- **Rule**: any change to `BUILD.md` outside its initial creation requires an accompanying `decisions/` entry.
- **User edits**: allowed. If the edit is substantive, write a companion `decisions/` entry so the "why" is recorded.

#### `CLAUDE.md`

- **Writes**: `/metis:init` only, and only between its delimiters (`<!-- metis:start -->` / `<!-- metis:end -->`). Content outside the delimiters is preserved.
- **User edits**: fully allowed outside the delimiters. Inside the delimiters, edits will be overwritten when `/metis:init` re-runs.

#### `.gitignore`

- **Writes**: `/metis:init` only, and only between its delimiters (`# <!-- metis:start -->` / `# <!-- metis:end -->`).
- **User edits**: fully allowed outside the delimiters. Inside the delimiters, edits will be overwritten when `/metis:init` re-runs.

### `docs/`

- **Writes**:
  - `/metis:reconcile` creates `SYNTHESIS.md`, `INDEX.md`, `CONTRADICTIONS.md`, `QUESTIONS.md`, `RESOLVED.md`.
  - `/metis:walk-open-items` updates the relevant source doc for each resolved item and moves the item from `CONTRADICTIONS.md` / `QUESTIONS.md` to `RESOLVED.md`.
- **Subagents**: do not write to `docs/` by default. Exception: a subagent dispatched by `/metis:reconcile` as a scalpel for compressing a single dense doc may write to the one file it was assigned.
- **User edits**: source docs are expected to be user-written; edits to reconcile outputs are allowed but will be overwritten on the next `/metis:reconcile` unless `/metis:sync` has picked them up first.
- **`RESOLVED.md`**: minimal-pointer archive. Never loaded during a walk unless explicitly requested.

### `decisions/*.md`

- **Writes**: append-only. New files only. Metis never edits an existing decision.
- **Who creates**: `/metis:sync`, `/metis:log-work`, and the main session when a doc or `BUILD.md` change warrants a standing record.
- **Subagents**: never. Task-level subagents record observations in the task's Notes; if something warrants a decision, the parent session writes it.
- **Superseding**: a new decision names the superseded file in its Context. The old decision is not modified.
- **User edits**: allowed, but editing an existing decision breaks the "decisions are a stable historical record" property. The right move for a changed position is a new decision that supersedes the old one.

### Task files (`tasks/*.md` or `epics/*/tasks/*.md`)

- **Writes**:
  - Task-generation commands (`/metis:generate-tasks`, `/metis:feature`) at creation.
  - `/metis:implement-task` — only the task file whose id was passed in, updating `status` and appending to Notes. Runs in the main session; the write restriction is prompt-level discipline rather than a tool restriction.
  - The `task-reviewer` subagent — only the task file it was reviewing, appending review findings to Notes.
  - `/metis:sync` — updates fields when upstream specs change. Requires user approval and a decision entry. `in-progress` tasks require explicit confirmation. `done` tasks are never edited — drift becomes a new task or a superseding decision.
  - `/metis:log-work` — updates fields to reflect code written outside the workflow; verifies against `git diff`.
- **Commands and subagents besides the assigned one**: never. `/metis:implement-task` does not touch other task files, even if "obviously related"; the reviewer subagent does not touch task files it was not dispatched against.
- **User edits**: allowed on any field. `id` and `title` are stable by default because other artifacts refer to them; if they change, reconcile via `/metis:log-work` or a resync. See `frontmatter-schema.md`.

### `epics/<name>/EPIC.md`

- **Writes**: `/metis:epic-breakdown`, `/metis:promote-to-epics`, `/metis:sync`.
- **Subagents**: never. (The two task-level subagents — `task-planner` and `task-reviewer` — *read* the parent `EPIC.md` when the task lives under an epic but do not write to it. `/metis:implement-task`, which runs in the main session, also reads it and does not write to it.)
- **User edits**: allowed. Status transitions (`pending` / `in-progress` / `done`) are expected to be manual edits.

### `epics/<name>/retro.md`

- **Writes**: `/metis:epic-retro` only, at epic close.
- **Subagents**: never.
- **User edits**: allowed — retros are meant to be read and annotated.

### `scratch/CURRENT.md`

- **Writes**: the main (parent) session.
- **Subagents**: never. A subagent has no visibility into the full session and can corrupt continuity.
- **When**: updated at session end by `/metis:session-end`. Small in-session updates are fine but should be infrequent.
- **User edits**: allowed. Expect the next `/metis:session-end` to rewrite substantial portions.

### `scratch/questions.md`

- **Writes**: main session. Committed. Resolved questions are removed at `/metis:session-end`.
- **Subagents**: never.
- **User edits**: allowed — adding, removing, or reordering questions directly is expected.

### `scratch/plans/<id>.md`

- **Writes**: the `task-planner` subagent only. Gitignored.
- **Lifecycle**: written by `/metis:plan-task`; consumed by `/metis:implement-task`; ignored after merge.
- **User edits**: allowed between plan and implementation — hand-editing the plan is a supported way to redirect the implementer.

### `.metis/`

- **Writes**: `/metis:init` (and future upgrade commands) writes `.metis/config.yaml`, `.metis/version`, `.metis/MANIFEST.md`, `.metis/conventions/*`, `.metis/templates/*`.
- **Subagents**: never.
- **User edits**: allowed. `.metis/config.yaml` is the one the user is most likely to touch (project settings like `spec_version`). Edits to convention and template files are allowed too but take effect on the user's local install — they will diverge from upstream Metis.

### `.claude/`

- **Writes**: `/metis:init` (and future upgrade commands) writes `.claude/skills/metis/*/SKILL.md` (the 21 primary skills, some with `references/` subdirs containing per-primary references) and `.claude/agents/metis/*`. The plugin-root `references/` directory (multi-caller and subagent-only references) is also created.
- **Subagents**: never.
- **User edits**: allowed — customizing a command or skill prompt for a specific project is supported. The same "diverges from upstream" caveat applies.
- **`.claude/commands/`**: Metis writes nothing here as of the skills-format migration. Claude Code still accepts command files there, but Metis's own commands live as command-register SKILL.md files under `.claude/skills/metis/`. See Refinement 12 in the handoff.

## Doc-change propagation

When a file in `docs/` changes:

1. The doc change is the source of truth for intent.
2. If `BUILD.md` is affected, it is updated via `/metis:sync` with a decision entry.
3. If downstream epics or tasks are affected, `/metis:sync` walks the cascade (batching cosmetic edits, walking substantive ones one at a time).
4. `done` tasks are never edited in place; drift becomes a new task or a superseding decision.
5. `in-progress` tasks require explicit confirmation before editing.

## Command-prompts convention

**The canonical source is `.metis/conventions/command-prompts.md`** — a runtime-shipped convention file. Commands and subagents reference that file by path; the four rules are not restated in command or subagent prompts, and they are not canonical in this doc either. This section exists as a design-time orientation pointer — if you are reading this doc to understand Metis, you should know the convention exists and where it lives — but the rules themselves are in the convention file.

Keeping the canonical rules in `.metis/conventions/` rather than in `docs/` is deliberate: runtime artifacts (skills, subagents, templates, conventions) ship with a Metis install; `docs/` is development-only. A pointer from a runtime file into `docs/` would break the moment Metis is packaged or the user clones without the docs directory.

### Summary (not canonical)

A substantive Metis skill or subagent that accepts a trailing free-text prompt references `.metis/conventions/command-prompts.md` and follows the four rules there — augment / flag scope expansion / acknowledge use / resolve named skills — treating the prompt as ephemeral. Six skills are purely mechanical (`/metis:pick-task`, `/metis:session-start`, `/metis:skeleton-plan`, `/metis:pushback`, `/metis:rebaseline`, `/metis:init`): they silently accept and ignore trailing prompts and do not reference the convention. Whether a given skill is mechanical or substantive is a property of the skill, not of the convention — the convention does not look up at its callers.

## Context budget

Metis's other load-bearing property is that a fresh session can get oriented with a small, well-scoped read. Bloated loads defeat that as surely as untrustworthy files do. These rules govern *what loads where* — a companion to the file-by-file write rules above. They are targets, not hard ceilings; occasional overage is fine, a pattern of overage means a refactor.

### Per-load targets

- **Always-on** (the `metis:start` / `metis:end` section of `CLAUDE.md`): ≤2k tokens. This is the only content every session pays for unconditionally. Keep it a pointer to the workflow, not a primer on it.
- **Per-command starter** (a command's prompt + the one skill it triggers + any convention that skill references): ≤5k tokens. Under this budget a command is cheap to invoke; over it, every downstream read is taxed.
- **Any single `SKILL.md`**: ≤~2500 words / ~3k tokens. A longer skill is almost always two skills, or is restating rules that belong in a convention.

### Skill reading diet

- A `SKILL.md` names at most two "read first" files (typically references). Anything else is described (with a pointer) and loaded only if the agent decides it needs to.
- References cite conventions, not other references. Cross-reference knowledge duplication is preferred to cross-reference loading — it keeps each reference's cost predictable.
- Convention files that run long (`frontmatter-schema.md` in particular) are **never bulk-loaded at runtime**. References that need a rule from them quote the specific rule inline.
- Counter-examples in `examples/` directories are *described* in the parent skill or reference, not prescribed as reads. The one-liner about *what's wrong* carries the educational value; loading the bad file just spends context.

### Corpus access patterns

- **`decisions/`** is a grep-only corpus. Never listed, never bulk-read. A mature project accumulates dozens to hundreds of decisions; enumeration is a token bomb. Find by slug or by content match.
- **`docs/RESOLVED.md`** is archive-only, as noted above. Not loaded during a walk unless explicitly requested.
- **Task-file excerpts** (per `writing-a-task-file`) quote the *minimum relevant passage* of a source doc, not the whole section. A task file that grows past ~1200 words usually has oversized quotes or is doing too much.

### Subagents as context firewalls

Task-level subagents exist partly for tool-restriction enforcement (above), but equally for context isolation. Plan and review each involve heavy reads — the task file, referenced docs, the plan, diffs — that return as a compressed summary to the main session; dispatching a subagent lets that reading happen in a fresh window and the main session's context grows by the summary, not by the inputs. The reviewer additionally depends on fresh context for *independence*: a reviewer that had seen the implementation's reasoning is not a reviewer.

Implementation is the exception. `/metis:implement-task` runs in the main session because the main session wants to see what happens during implementation — the user may interject, and the eventual follow-ups would re-derive context that a subagent's return had just compressed away. The write restrictions that the subagent would have enforced structurally (no writes to `BUILD.md`, `scratch/CURRENT.md`, `decisions/`, or other task files) are carried as prompt-level discipline in the command instead. See Refinement 10 in the handoff for the reasoning.

The corollary as a design heuristic for new commands and skills: if the work is a one-shot heavy read that produces a single artifact and returns a summary, dispatch a subagent. If the work wants interactivity, wants the user watching, or benefits from the main session knowing what happened in detail, keep it in the main session and carry the discipline in the command prompt.

### Session-level discipline

Prefer ending a session with `/metis:session-end` over riding auto-compact. Auto-compaction is lossy in ways Metis does not control; `scratch/CURRENT.md` is lossy in ways it does. Keep `CURRENT.md` under ~1k tokens so the next session's rehydration is cheap.

## When in doubt

If a rule here conflicts with the behavior a command or subagent seems to want, the correct response is **stop and flag the conflict**, not silently work around the rule. These rules encode the properties that make Metis trustworthy.
