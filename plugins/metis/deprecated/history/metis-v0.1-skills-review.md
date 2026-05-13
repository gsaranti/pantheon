# Metis v0.1 — Holistic Skills Review

A pre-ship review of all fifteen skills in `template/.claude/skills/metis/`, organized around the four criteria called out in the review charter: purpose/principle alignment, token efficiency, co-work discipline, and read-file consistency. The review assumes the handoff doc (`docs/metis-v0.1-handoff.md`) as the canonical source for what Metis is and the v0.1 convention set as the current operating spec.

All counts below are against the shipped skill files on disk (15 skills, ~16,200 words total, average 1,082 words per skill).

---

## Overall assessment

The skill set is in very good shape. The prose register is consistent and artifact-anchored, the structural template (intro → failure-mode pair → Read first → judgment sections → Sizing-as-feedback → Examples) is followed by every file, and the load-bearing teaching in each skill is justifiable against its artifact. No skill is primarily character-shaping; no skill is primarily ceremony.

The issues that remain are small, mostly about consistency rather than content. One skill ships without an example (`writing-build-spec`). One skill's "Read first" directives technically drifted into command-layer territory as originally flagged by `write-rules.md` — the tension is now resolved by relocating that file to `docs/metis-write-rules.md` (see Criterion 4). Three skills carry minor prose redundancy that could be pruned without loss. None of these are ship-blockers; addressing them would be a short, low-risk pass.

The overall register sits where the handoff asks it to: skills teach *about the artifact*, not *about Claude*. "Structure the project, not the agent" reads cleanly out of the 15 files taken together.

---

## Criterion 1 — Alignment with purpose and principles

Every skill passes. No file drifts into trying to reshape how Claude thinks; every judgment section anchors its advice to a property of the artifact (Goal outcome-framing, scope reduction being visible in the Notes block, exit criterion being one testable condition, etc.). The "Two failure modes pull against each other" framing that opens every skill sets the register early — both over- and under-doing a thing are real failures, and the agent's job is to land between them — and this framing is what keeps the skills from becoming prescriptive.

Specific alignments worth calling out:

- `planning-a-task` explicitly rejects forced TDD in its "Test approach without forced TDD" section. This is the load-bearing "we don't reshape the agent" principle in operation — tests-first is one of three registers the plan can pick per step.
- `walking-open-items` carries the Metis-as-partner ethos strongest: "Asking the user vs. deciding" names a concrete downstream-reach threshold for what the agent lands alone vs. what must be confirmed by the user.
- `writing-decisions` explicitly gates decision-writing with "would a reader six months from now benefit from finding this on its own?" — the skill refuses to generate a decision for local implementation choices, which is the append-only-decisions principle protecting itself from noise.
- `propagating-spec-changes` is status-aware by task state (`done` never edits in place, `in-progress` requires confirmation) which is the task-scoped-context principle applied to change management.

No skill carries orchestration content ("then dispatch the reviewer," "then call session-end") — that all correctly stays in command territory.

**One borderline case**: `reconciling-docs`'s "Reading the corpus well" section teaches a specific multi-pass reading methodology rather than just artifact properties. The reading cadence is genuinely what produces detectable contradictions (the artifact's quality emerges from the reading pattern), so it is justifiable as artifact-shaping teaching. But it is the closest any skill gets to prescribing Claude's approach, and if the line ever moved, this is where to tighten first.

---

## Criterion 2 — Every sentence earns its place

Most skills are already tight. A few patterns carry minor fat:

**Repeated rhetorical structure.** Every skill opens with a "two failure modes pull against each other" paragraph. This is a genuinely useful framing and its repetition is worth the tokens (it sets the register) — but each instance takes 3–5 sentences, and a few are slightly verbose even by that standard. `honest-scope-reporting`'s opener is the longest of the 15 and could lose one sentence ("Without that block, reductions that land in the surrounding narrative are invisible to the reader who receives the result" re-states the under-reporting case the next paragraph already opens with).

**`reconciling-docs` — pass-cadence paragraphs.** The "Reading the corpus well" section has four paragraphs doing closely related work: two-pass minimum, writing INDEX.md under construction, pass-end criterion, between-pass state. The last two restate each other ("A pass ends when the next passage would not change INDEX.md..." and "Pass boundaries are natural context resets..."). One of them could be cut with no loss.

**`honest-scope-reporting` — duplicated "don't invent" reminders.** The "An empty report is the common case..." reminder appears under *Artifact shape*, and the "Manufacturing entries to fill each block..." reminder appears under *Sizing as feedback*. They teach the same thing. Collapse into one.

**`writing-decisions` — "Permanence and preview" framing.** This section is effectively instructing the *calling command* that it must preview decisions before writing. It is close to command-layer content living in a skill. The property it teaches (decisions are permanent, so preview matters) does belong in the skill, but the paragraph about upstream-approval-not-covering-framing reads like it was written to a command author, not to a skill reader. Could be two sentences shorter and tighter.

**`logging-external-work` — longest skill (1,476 words).** The length is defensible — the reconciliation teaches genuinely distinct judgment across description-vs-diff, per-task claim types, done-verification, task CRUD, retroactive tasks, and architecture-triggered decisions. Each section does work the others do not. But the intro paragraph about source-of-truth asymmetry is re-stated in "Reading the description and the diff" — collapse to one statement of the asymmetry rule.

**`propagating-spec-changes` — second-longest (1,282 words).** Also defensible for the same reason, and the tight "Detection is a scan, not a walk" / "Bulk-approving a substantive edit is the failure mode this classification exists to prevent" lines are exactly the register the skill wants. Minor: "Cascade by epic state" mirrors "Cascade by task status" almost clause-for-clause. There's a lighter way to handle this — state the task rules, then say "epic state follows the same rules in `pending`/`in-progress`/`done`, with scope and exit-criterion shifts as the substance" — saving ~80 words.

**Skills that are already at or below sizing budget and need no pruning**: `writing-a-task-file` (869w), `session-handoff` (877w), `decomposing-work-into-tasks` (988w), `writing-decisions` (973w after minor Permanence cut).

Net estimate: a pruning pass could recover ~800–1,200 words (roughly 5–7% of total skill content) without changing any artifact output quality.

---

## Criterion 3 — Partner not driver (co-work discipline)

Every skill honors this principle, and several carry it well enough to be exemplars.

Patterns across the 15 files:

- **Ambiguity routing is consistent.** Every skill that faces source ambiguity distinguishes *local* ambiguity (handleable inline — a TODO flag in Notes, a question in `scratch/questions.md`) from *structural* ambiguity (surface upstream — decomposition, decision, direct conversation). The taxonomy shows up in `decomposing-work-into-tasks`, `decomposing-build-into-epics`, `writing-a-task-file`, `writing-an-epic-file`, and `planning-a-task`, always with the same shape. Good consistency.
- **Push-back is explicit.** `planning-a-task` has a dedicated "Pushing back on the task file" section. `reconciling-docs` ends with "Zero items is usually a miss" — the skill refuses to rubber-stamp clean docs. `honest-scope-reporting` treats scope reduction as a finding, not a concession.
- **User authority preserved at thresholds.** `walking-open-items` "Asking the user vs. deciding" defines when the agent should land a resolution alone vs. confirm. `propagating-spec-changes` requires confirmation before editing `in-progress` tasks. `writing-decisions` refuses to write a decision for things that aren't decisions.
- **"Metis reconciles, does not enforce."** `logging-external-work` is the load-bearing skill for this: the user's description is the source of truth for intent, the diff is the source of truth for facts, and the skill surfaces daylight rather than quietly picking a side. This is partner-shaped discipline in operation.

No skill carries "you must," "always," or "never" content that locks out the user's judgment. The rules that do exist ("one decision per accepted cascading change," "Notes stays empty at creation") are about the artifact's shape, not about constraining the user.

**Minor observation**: `planning-a-task`'s "Pushing back on the task file" section is the clearest articulation of the partner principle in action. The equivalent "I don't have a good read" register in `walking-open-items` is also strong. Neither principle is named as such in any skill (they are enacted rather than labeled), which is probably correct — labeling them would drift toward meta-framing.

---

## Criterion 4 — Consistency in how skills direct the agent to read files

This is the review's most substantive finding. The pattern of `## Read first` sections is broadly consistent but carries a real tension with `write-rules.md`.

### The surface consistency

Fourteen of fifteen skills have a `## Read first` H2. The section typically names (a) required inputs for the artifact, (b) any convention files that carry the structural spec, and (c) on-demand loads for field-level lookups. The phrasing is stable: "Load X on demand when..." appears in five skills with near-identical wording.

### Shape-of-artifact ownership varies

Skills split into two groups:

- **Convention-backed artifacts** (5 skills): `writing-a-task-file`, `writing-an-epic-file`, `writing-decisions`, `decomposing-work-into-tasks`, `decomposing-build-into-epics`. These point at a `.metis/conventions/*.md` file for structural spec and carry judgment only.
- **Skill-owned artifacts** (10 skills): everything else. These describe the artifact's shape inline, typically under an `## Artifact shape` H2 (`reconciling-docs`, `planning-a-task`, `reviewing-against-criteria`, `honest-scope-reporting`, `session-handoff`, `writing-retros`) or inline in judgment sections (`writing-build-spec`, `walking-open-items`, `propagating-spec-changes`, `logging-external-work`).

This split is defensible — not every artifact needs a convention file, and creating one per niche artifact would inflate `.metis/conventions/`. But the pattern should be named so it doesn't feel arbitrary.

### The layer-drift tension (resolved by relocating write-rules to `docs/`)

The original `write-rules.md` said: *"A skill names the kinds of inputs the artifact requires ('a body of work plus the source docs it references') but does not prescribe specific files, loading sequence, or session orchestration."*

Multiple skills do prescribe specific files by path in their `## Read first` sections (`.metis/conventions/task-format.md`, `.metis/templates/task.md`, etc.), which strictly read was layer drift — the specific load list is supposed to live in the invoking command, not in the skill.

This was resolved by recognizing that `write-rules.md` was miscategorized: it is a design-time narrative about layer responsibilities and the framework's write discipline, not a runtime file-format spec consulted by a skill. The file was moved to `docs/metis-write-rules.md`. The conventions folder is now coherent — four file-format specs each referenced by file path from at least one skill — and the layer-responsibilities paragraph in the relocated reference is now framework-author guidance rather than a rule the skills are violating. Skills naming specific convention and template files by path is the supported pattern.

### Specific inconsistencies to fix

- **`writing-build-spec` has no `## Examples` section and no example file.** Every other skill ends with "Read this before your first X in a session" pointing to an example. `writing-build-spec` simply stops after "Sizing as feedback." This is the clearest single inconsistency across the set. Either add `examples/good-build-spec.md` (a clean BUILD.md fragment) or add an explicit one-line note explaining why no example is shipped (e.g., "BUILD.md content is project-shaped enough that a generic example would mislead more than it teaches" — if that is the real reason).
- **`writing-an-epic-file` does not name `frontmatter-schema.md` as an on-demand load.** `writing-a-task-file` does ("Load `.metis/conventions/frontmatter-schema.md` on demand when populating frontmatter..."). Epic frontmatter exists and is non-trivial; the same on-demand reference would be consistent.
- **`reconciling-docs` has `## Read first` but no required reads.** It says "There is no convention file for the reconcile artifacts; the on-disk shape is defined in *Artifact shape* below." This is correct but reads oddly — `## Read first` that contains no read targets is a header with nothing under it. Consider either removing the section for this skill or phrasing it as "This skill owns its artifact shape — see *Artifact shape* below" so the section has content.

### Naming consistency (already good)

All 15 skills start their description field with "Reference for..." Frontmatter is uniform (name, description, `disable-model-invocation: true`). No skill carries a "Used by" section. Example-pointer language is identical across skills with examples ("**Read this before your first X in a session.**"). Confirmed clean.

---

## Recommended actions

In priority order:

1. **Add an example to `writing-build-spec` or explain its absence.** Unambiguous inconsistency; easiest fix in the set.
2. ~~**Resolve the skills-prescribe-files tension in `write-rules.md`.**~~ **Done.** Resolved by moving `write-rules.md` to `docs/metis-write-rules.md` — it was a design-time narrative misfiled in the runtime conventions folder. The relocation makes the conventions folder coherent (file-format specs only) and reframes the layer-responsibilities paragraph as framework-author guidance rather than a rule the skills are violating.
3. **Add `frontmatter-schema.md` as on-demand load to `writing-an-epic-file`.** One-line edit.
4. **Prune the identified redundancies** in `reconciling-docs` (pass-cadence paragraphs), `honest-scope-reporting` (duplicate "don't manufacture" reminders), `writing-decisions` (Permanence and preview tightening), `logging-external-work` (source-of-truth re-statement), and `propagating-spec-changes` (cascade-by-epic-state mirroring). Combined: ~800–1,200 words recovered, no output-quality loss.
5. ~~**Consider whether the skill-owned-artifact pattern should be named.**~~ **Done.** One sentence added to the handoff's Skills section opener naming the ten-skill-owned / five-convention-backed split and the reason (convention files exist for formats shared across multiple skills and commands, not per-artifact).

Items 1–3 are each a single-file edit. Items 4–5 are a short dedicated pass that could be done in one sitting.

No finding in this review calls for a structural rework. The skills layer is ready to carry subagents and commands on top of it.
