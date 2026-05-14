#!/usr/bin/env python3
"""Generate Metis's Codex install tree from its canonical Claude source.

For the Metis plugin, `.claude-code/` is the canonical source of truth:
each skill folder under .claude-code/skills/ is fully self-contained
(SKILL.md plus a local references/ that holds both markdown reference
docs and any shell scripts the skill runs), with cross-skill shared
markdown at .claude-code/references/. Claude installs `.claude-code/`
directly (the Claude marketplace's `source` field points there); this
script reads from it to emit a parallel Codex install at `.codex/` that
follows Codex's "self-contained skill folder" convention:

  - Each .codex/skills/<name>/ is a near-verbatim copy of the source
    skill folder (so local references/, including any scripts living
    there, ride along intact), with ${CLAUDE_PLUGIN_ROOT}/references/...
    paths in SKILL.md rewritten to point at the skill's local references/
    copy of each shared reference file.
  - Each .codex/skills/<name>/agents/openai.yaml carries the Codex
    equivalent of Claude's disable-model-invocation: true flag.
  - Each .codex/agents/<name>.toml is a TOML rewrite of the Claude
    subagent .md, with ${CLAUDE_PLUGIN_ROOT}/references/... pointers
    inlined into developer_instructions (Codex agents are single files,
    no sibling dirs).

Scoped writes — the script only touches .codex/skills/ and .codex/agents/.
Everything else under .codex/ is preserved across runs. In particular,
.codex/.codex-plugin/plugin.json is the Codex per-plugin manifest, hand-
maintained by the plugin author; this script never reads, writes, or
removes it.

This script is intentionally Metis-specific — it knows Metis's layout
(shared markdown at .claude-code/references/, skill-local content at
.claude-code/skills/<name>/references/). Other plugins in the Pantheon
marketplace can each have their own conversion script tailored to their
layout (e.g., gen-<plugin>-codex.py).

Usage:
    python3 scripts/gen-metis-codex.py           # regenerate .codex/{skills,agents}/
    python3 scripts/gen-metis-codex.py --check   # exit 1 if those subtrees are stale
"""

from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — all hardcoded to Metis's known layout
#
# .claude-code/ is the canonical source-of-truth for both runtimes: Claude
# installs it directly (the Claude marketplace points its `source` field
# there), and this script reads from it to emit the Codex install at .codex/.
# .codex/ has only two regenerated subtrees — skills/ and agents/. Anything
# else inside .codex/ (in particular .codex-plugin/, which carries Codex's
# per-plugin manifest) is hand-maintained and preserved across runs.

ROOT = Path(__file__).resolve().parent.parent
METIS = ROOT / "plugins" / "metis"
CLAUDE_SRC = METIS / ".claude-code"
SKILLS_SRC = CLAUDE_SRC / "skills"
AGENTS_SRC = CLAUDE_SRC / "agents"
REFERENCES_SRC = CLAUDE_SRC / "references"
CODEX_OUT_DEFAULT = METIS / ".codex"

# Subtrees of CODEX_OUT_DEFAULT that this script owns. Used both to scope
# rebuild (rmtree + recreate just these) and to scope --check comparisons
# (don't compare .codex-plugin/ etc.).
CODEX_OWNED_SUBDIRS = ("skills", "agents")

# ---------------------------------------------------------------------------
# Reference path patterns.
#
# SKILL_REF_RE matches any backtick-wrapped reference path inside SKILL.md,
# in either of two forms:
#   `references/X.(md|sh)`                   — skill-local (.md or .sh)
#   `${CLAUDE_PLUGIN_ROOT}/references/X.md`  — shared cross-skill markdown
#
# Group 1 captures whether the shared prefix was present (truthy iff the path
# is a shared ref that needs to be copied into the skill folder). Group 2
# captures the filename. Backticks are mandatory: only code-span occurrences
# get rewritten — references mentioned in plain prose or non-code contexts
# are left alone.
#
# Both forms get the "this skill's `references/X`" rewrite in the Codex
# output. The Codex tree puts every skill's local references/ and every
# shared markdown copy in the same place (the skill's own references/), so a
# single rendered form is correct for both inputs and keeps the output
# consistent across paths.
SKILL_REF_RE = re.compile(
    r"`(\$\{CLAUDE_PLUGIN_ROOT\}/)?references/([\w.\-]+\.(?:md|sh))`"
)

# AGENT_REF_RE is the narrower pattern used when porting agents — they only
# ever reference shared markdown via ${CLAUDE_PLUGIN_ROOT}/, and the rewrite
# is in-prose ("the X reference embedded below") rather than a code-span, so
# the surrounding backticks are optional and consumed.
AGENT_REF_RE = re.compile(
    r"`?\$\{CLAUDE_PLUGIN_ROOT\}/references/([\w.\-]+\.md)`?"
)

# Claude `tools:` frontmatter → Codex `sandbox_mode`.
# Any agent that needs Bash (e.g., metis-task-reviewer for `git diff`,
# verification commands) needs workspace-write because Codex's sandbox is
# coarser than Claude's per-tool allowlist. Everything else stays read-only.
TOOL_REQUIRES_WORKSPACE_WRITE = {"Bash"}
DEFAULT_SANDBOX = "read-only"


# ---------------------------------------------------------------------------
# Frontmatter

def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return ({key: value}, body_after_frontmatter).

    Handles only the simple top-level scalar form Metis uses. Values are kept
    as strings; quoting is preserved verbatim.
    """
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm_block = text[4:end]
    body = text[end + len("\n---\n"):]
    fm: dict[str, str] = {}
    for line in fm_block.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, body


def serialize_frontmatter(fm: dict[str, str]) -> str:
    if not fm:
        return ""
    lines = ["---"]
    for k, v in fm.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers

def map_tools_to_sandbox(tools_str: str) -> str:
    """`Read, Glob, Grep, Bash` → 'workspace-write'; otherwise 'read-only'."""
    if not tools_str:
        return DEFAULT_SANDBOX
    tools = {t.strip() for t in tools_str.split(",")}
    if tools & TOOL_REQUIRES_WORKSPACE_WRITE:
        return "workspace-write"
    return DEFAULT_SANDBOX


def build_skill_command_re(skill_names: list[str]) -> re.Pattern[str]:
    """Pattern matching Claude `/skill-name` slash commands for rewrite to
    Codex's `$skill-name` form.

    Built from the live skill directory listing rather than a hardcoded
    pattern, so the rewrite only fires on exact known skill names — never
    on an arbitrary `/foo` prefix. Names sort longest-first under
    alternation so the most specific match wins if a future skill name is
    ever a prefix of another (Python's `re` alternation is leftmost, not
    longest).

    The `(?<!\\w)` lookbehind keeps the rewrite from firing inside path
    fragments like `plugins/metis/skills/metis-init/SKILL.md`, where the
    slash is a path separator rather than a command introducer. The
    trailing `\\b` stops the match at a word boundary so we don't bleed
    into a longer identifier (e.g., a hypothetical `/metis-init-extra`
    would not be partially matched as `/metis-init`).
    """
    if not skill_names:
        # `(?!)` is the standard "never matches" regex — preserves the type
        # signature so callers don't need an Optional[Pattern] guard.
        return re.compile(r"(?!)")
    sorted_names = sorted(skill_names, key=len, reverse=True)
    alt = "|".join(re.escape(name) for name in sorted_names)
    return re.compile(rf"(?<!\w)/({alt})\b")


def rewrite_skill_commands(text: str, skill_command_re: re.Pattern[str]) -> str:
    """Apply the Claude → Codex slash-command rewrite to a block of text."""
    return skill_command_re.sub(lambda m: f"${m.group(1)}", text)


def src_for_ref(filename: str) -> Path:
    """Resolve a shared-reference filename against .claude-code/references/."""
    return REFERENCES_SRC / filename


def toml_escape_basic(s: str) -> str:
    """Escape a string for a TOML basic (double-quoted) string."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


# ---------------------------------------------------------------------------
# Skill porting: copy folder, rewrite paths, copy referenced files, add openai.yaml

def port_skill(skill_src: Path, out_root: Path, skill_command_re: re.Pattern[str]) -> None:
    # Validate before doing any work: copying a folder and then erroring on a
    # missing SKILL.md would leave a half-populated output directory.
    if not (skill_src / "SKILL.md").exists():
        raise RuntimeError(f"{skill_src} has no SKILL.md")

    # generate() wipes the entire out_root before calling port_skill, so
    # skill_out is guaranteed not to exist yet. dirs_exist_ok=True is kept as
    # cheap insurance against future refactors of generate().
    skill_out = out_root / "skills" / skill_src.name
    shutil.copytree(skill_src, skill_out, dirs_exist_ok=True)

    # Apply the slash-command rewrite to the markdown refs that just rode
    # along via copytree. Shared markdown refs (planted by the loop below)
    # already get this same treatment; skill-local ones used to ride along
    # untouched, which left the Codex tree mixing /metis-X and $metis-X
    # syntax in the same skill's docs. claude-block.md is excluded — it's
    # the verbatim body of the user's CLAUDE.md block, and that block is
    # meant to keep Claude's /metis-X syntax for the Claude user reading
    # it. Shell scripts are intentionally not rewritten: they sometimes
    # carry user-facing slash-command strings that the script author wants
    # preserved as-is, and addressing the script-side mismatch properly is
    # a separate concern.
    local_refs_dir = skill_out / "references"
    if local_refs_dir.is_dir():
        for md_path in local_refs_dir.glob("*.md"):
            if md_path.name == "claude-block.md":
                continue
            md_path.write_text(
                rewrite_skill_commands(md_path.read_text(), skill_command_re)
            )

    # From here on, operate on the output copy. The source is canonical and
    # must not be touched.
    skill_md = skill_out / "SKILL.md"
    text = skill_md.read_text()

    # Collect shared-reference filenames that need to be copied into the
    # skill folder. Bare `references/X` references (skill-local) get the
    # same prose rewrite but don't need copying — they already ride along
    # via the copytree above.
    referenced: set[str] = set()

    def replace(m: re.Match[str]) -> str:
        is_shared = m.group(1) is not None
        filename = m.group(2)
        if is_shared:
            referenced.add(filename)
        # The rewritten path is relative to the skill folder, not the repo
        # root or CWD — Codex has no way to infer that from the path alone,
        # so we prepend "this skill's" to disambiguate. Capitalize when the
        # match starts a line (e.g., bullet-style fragments under "## Read
        # first" headings) so the sentence reads naturally; otherwise keep
        # it lowercase for mid-sentence flow. The rewritten path stays a
        # code-span — in skill SKILL.md, the path was always a code-span,
        # and the rewritten relative path should be too.
        at_line_start = m.start() == 0 or text[m.start() - 1] == "\n"
        prefix = "This skill's" if at_line_start else "this skill's"
        return f"{prefix} `references/{filename}`"

    new_text = SKILL_REF_RE.sub(replace, text)

    # Translate Claude's `/skill-name` slash-command references into Codex's
    # `$skill-name` form. Codex addresses skills with `$`; leaving `/` in
    # the SKILL.md would surface the wrong invocation syntax to the agent.
    new_text = rewrite_skill_commands(new_text, skill_command_re)

    # Drop disable-model-invocation: true — Codex equivalent goes in openai.yaml.
    fm, body = parse_frontmatter(new_text)
    fm.pop("disable-model-invocation", None)
    new_text = serialize_frontmatter(fm) + body

    skill_md.write_text(new_text)

    # Copy each referenced shared-markdown file into the skill's local
    # references/. The slash-command rewrite is applied along the way —
    # Codex reads these files too, and mixed `/skill` / `$skill` syntax
    # across the same skill folder would be confusing. Skipped entirely
    # when the skill has no shared refs: a skill with no local references/
    # in source and no shared-ref mentions in SKILL.md (e.g., metis-session-
    # start) ends up with no references/ folder rather than an empty one.
    if referenced:
        refs_dir = skill_out / "references"
        refs_dir.mkdir(exist_ok=True)
        for filename in sorted(referenced):
            src = src_for_ref(filename)
            if not src.exists():
                raise RuntimeError(
                    f"{skill_src.name}/SKILL.md references {filename}, "
                    f"but {src} does not exist."
                )
            content = rewrite_skill_commands(src.read_text(), skill_command_re)
            (refs_dir / filename).write_text(content)

    # Codex's "explicit invocation only" equivalent of disable-model-invocation.
    yaml_dir = skill_out / "agents"
    yaml_dir.mkdir(exist_ok=True)
    (yaml_dir / "openai.yaml").write_text(
        "policy:\n  allow_implicit_invocation: false\n"
    )


# ---------------------------------------------------------------------------
# Agent porting: convert .md → .toml, inline references into developer_instructions

def port_agent(agent_md: Path, out_root: Path, skill_command_re: re.Pattern[str]) -> None:
    name = agent_md.stem
    out_path = out_root / "agents" / f"{name}.toml"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    text = agent_md.read_text()
    fm, body = parse_frontmatter(text)

    # Inline references: each ${CLAUDE_PLUGIN_ROOT}/references/... reference
    # is replaced in-prose with a pointer to the inlined section, then the
    # file content is appended below as a "## Reference: <name>" block.
    referenced: list[str] = []
    seen: set[str] = set()

    def replace(m: re.Match[str]) -> str:
        filename = m.group(1)
        if filename not in seen:
            seen.add(filename)
            referenced.append(filename)
        # The regex consumed any surrounding markdown backticks, so the
        # replacement is plain prose with only the filename in backticks.
        return f"the `{filename}` reference embedded below"

    new_body = AGENT_REF_RE.sub(replace, body)

    for filename in referenced:
        src = src_for_ref(filename)
        if not src.exists():
            raise RuntimeError(
                f"agents/{name}.md references {filename}, "
                f"but {src} does not exist."
            )
        content = src.read_text().rstrip()
        new_body = new_body.rstrip() + f"\n\n## Reference: {filename}\n\n{content}\n"

    # Translate Claude's `/skill-name` slash commands into Codex's `$skill-name`
    # form. Applied after inlining so the rewrite covers both the agent's own
    # body and the inlined reference sections in one pass — Codex sees the
    # whole TOML as a single document, so the syntax has to be consistent
    # across it.
    new_body = rewrite_skill_commands(new_body, skill_command_re)

    toml_name = fm.get("name", name)
    description = fm.get("description", "")
    sandbox = map_tools_to_sandbox(fm.get("tools", ""))

    # Use TOML literal multi-line strings (''') so we don't have to escape
    # backslashes, double-quotes, or special characters in the body.
    body_text = new_body.lstrip("\n").rstrip()
    if "'''" in body_text:
        raise RuntimeError(
            f"agents/{name}.md body contains ''' — would break TOML literal "
            "string delimiter. Use a different escaping strategy."
        )

    out_lines = [
        f'name = "{toml_escape_basic(toml_name)}"',
        f'description = "{toml_escape_basic(description)}"',
        f'sandbox_mode = "{sandbox}"',
        "",
        "developer_instructions = '''",
        body_text,
        "'''",
        "",
    ]
    out_path.write_text("\n".join(out_lines))


# ---------------------------------------------------------------------------
# Orchestration

def generate(out_root: Path) -> None:
    # Only CODEX_OWNED_SUBDIRS are this script's territory. Everything else
    # under out_root (notably .codex-plugin/ with the hand-maintained Codex
    # manifest) is preserved across regenerations. ignore_errors covers FUSE
    # mounts that refuse unlink; subsequent copytree(dirs_exist_ok=True) and
    # write_text() will overwrite remaining files in place.
    out_root.mkdir(parents=True, exist_ok=True)
    for subdir in CODEX_OWNED_SUBDIRS:
        target = out_root / subdir
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        target.mkdir(parents=True, exist_ok=True)

    # Discover skill names up front so the slash-command rewrite pattern is
    # built from the live directory listing — a future skill folder is
    # picked up automatically; spurious `/foo` strings that don't match any
    # real skill name are left alone.
    skill_dirs = (
        sorted(p for p in SKILLS_SRC.iterdir() if p.is_dir())
        if SKILLS_SRC.is_dir() else []
    )
    skill_command_re = build_skill_command_re([p.name for p in skill_dirs])

    for skill_dir in skill_dirs:
        port_skill(skill_dir, out_root, skill_command_re)

    if AGENTS_SRC.is_dir():
        for agent_md in sorted(AGENTS_SRC.glob("*.md")):
            port_agent(agent_md, out_root, skill_command_re)


# ---------------------------------------------------------------------------
# --check mode: byte-identical comparison against the committed tree

def trees_equal(a: Path, b: Path) -> tuple[bool, list[str]]:
    """Return (equal, list_of_differences).

    Comparison is scoped to CODEX_OWNED_SUBDIRS — the only subtrees this
    script writes. Anything else under either tree (e.g., the hand-maintained
    .codex-plugin/ on the committed side) is ignored so --check doesn't
    flag the committed tree as stale on every CI run.
    """
    diffs: list[str] = []
    for subdir in CODEX_OWNED_SUBDIRS:
        _diff_walk(a / subdir, b / subdir, diffs)
    return (not diffs), diffs


def _diff_walk(a: Path, b: Path, diffs: list[str]) -> None:
    if not a.exists() and not b.exists():
        return
    if not a.exists():
        diffs.append(f"missing in generated: {b}")
        return
    if not b.exists():
        diffs.append(f"missing in committed: {a}")
        return
    cmp = filecmp.dircmp(a, b)
    for name in cmp.left_only:
        diffs.append(f"only in generated: {a / name}")
    for name in cmp.right_only:
        diffs.append(f"only in committed: {b / name}")
    for name in cmp.diff_files:
        diffs.append(f"differs: {a / name}  vs  {b / name}")
    for sub in cmp.common_dirs:
        _diff_walk(a / sub, b / sub, diffs)


# ---------------------------------------------------------------------------
# CLI

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--out",
        type=Path,
        default=CODEX_OUT_DEFAULT,
        help=f"Output directory (default: {CODEX_OUT_DEFAULT.relative_to(ROOT)})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare generated output against the committed tree; exit 1 if stale",
    )
    args = parser.parse_args()

    # Display path relative to ROOT when possible, absolute otherwise — so a
    # custom --out outside the repo doesn't crash the success message.
    try:
        display = args.out.relative_to(ROOT)
    except ValueError:
        display = args.out

    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_out = Path(tmp) / "codex"
            generate(tmp_out)
            equal, diffs = trees_equal(tmp_out, args.out)
            if equal:
                print(f"OK  {display} is up to date")
                return 0
            print(f"FAIL  {display} is stale — run `python3 scripts/gen-metis-codex.py`")
            for d in diffs[:20]:
                print(f"  {d}")
            if len(diffs) > 20:
                print(f"  ... and {len(diffs) - 20} more")
            return 1

    generate(args.out)
    print(f"OK  regenerated {display}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
