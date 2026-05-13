#!/usr/bin/env python3
"""Generate Metis's Codex-compatible plugin tree from its canonical Claude source.

For the Metis plugin (plugins/metis/), the Claude tree (skills/, agents/,
references/, .metis/scripts/ — all under plugins/metis/) is the source of
truth. This script reads it and emits plugins/metis/.codex/ — a parallel
tree that follows Codex's "self-contained skill folder" convention:

  - Each .codex/skills/<name>/ carries its own references/ and scripts/
    subdirectories, with ${CLAUDE_PLUGIN_ROOT}/... paths rewritten to
    skill-local relative paths.
  - Each .codex/skills/<name>/agents/openai.yaml carries the Codex
    equivalent of Claude's disable-model-invocation: true flag.
  - Each .codex/agents/<name>.toml is a TOML rewrite of the Claude
    subagent .md, with ${CLAUDE_PLUGIN_ROOT}/... references inlined into
    developer_instructions (Codex agents are single files, no sibling dirs).

This script is intentionally Metis-specific — it knows Metis's layout
(scripts at .metis/scripts/, references at references/, etc.). Other
plugins in the Pantheon marketplace can each have their own conversion
script tailored to their layout (e.g., gen-<plugin>-codex.py).

Usage:
    python3 scripts/gen-metis-codex.py           # regenerate plugins/metis/.codex/
    python3 scripts/gen-metis-codex.py --check   # exit 1 if stale (CI guard)
"""

from __future__ import annotations

import argparse
import filecmp
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — all hardcoded to Metis's known layout

ROOT = Path(__file__).resolve().parent.parent
METIS = ROOT / "plugins" / "metis"
SKILLS_SRC = METIS / "skills"
AGENTS_SRC = METIS / "agents"
REFERENCES_SRC = METIS / "references"
SCRIPTS_SRC = METIS / ".metis" / "scripts"
CODEX_OUT_DEFAULT = METIS / ".codex"

# ---------------------------------------------------------------------------
# Pattern: ${CLAUDE_PLUGIN_ROOT}/.metis/scripts/<name>.sh
#       or ${CLAUDE_PLUGIN_ROOT}/references/<name>.md
# Metis-specific: scripts live under .metis/scripts/ (a Metis convention),
# references live under references/ at the plugin root. The optional
# (?:\.metis/)? group handles both forms.
#
# Optionally captures the surrounding markdown backticks so we can rewrite the
# whole code-span (skill output re-wraps in backticks; agent output uses prose
# with only the filename in backticks).
PLUGIN_ROOT_RE = re.compile(
    r"`?\$\{CLAUDE_PLUGIN_ROOT\}/(?:\.metis/)?(scripts|references)/([\w.\-]+\.(?:sh|md))`?"
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


def src_for_ref(kind: str, filename: str) -> Path:
    """Resolve a (kind, filename) pair against Metis's canonical source dirs."""
    if kind == "scripts":
        return SCRIPTS_SRC / filename
    if kind == "references":
        return REFERENCES_SRC / filename
    raise ValueError(f"unknown ref kind: {kind}")


def toml_escape_basic(s: str) -> str:
    """Escape a string for a TOML basic (double-quoted) string."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


# ---------------------------------------------------------------------------
# Skill porting: copy folder, rewrite paths, copy referenced files, add openai.yaml

def port_skill(skill_src: Path, out_root: Path) -> None:
    # Validate before doing any work: copying a folder and then erroring on a
    # missing SKILL.md would leave a half-populated output directory.
    if not (skill_src / "SKILL.md").exists():
        raise RuntimeError(f"{skill_src} has no SKILL.md")

    # generate() wipes the entire out_root before calling port_skill, so
    # skill_out is guaranteed not to exist yet. dirs_exist_ok=True is kept as
    # cheap insurance against future refactors of generate().
    skill_out = out_root / "skills" / skill_src.name
    shutil.copytree(skill_src, skill_out, dirs_exist_ok=True)

    # From here on, operate on the output copy. The source is canonical and
    # must not be touched.
    skill_md = skill_out / "SKILL.md"
    text = skill_md.read_text()

    # Collect referenced (kind, filename) pairs while rewriting paths.
    referenced: set[tuple[str, str]] = set()

    def replace(m: re.Match[str]) -> str:
        kind, filename = m.group(1), m.group(2)
        referenced.add((kind, filename))
        # Re-wrap in backticks: in skill SKILL.md, the path was always a
        # code-span, and the rewritten relative path should be too.
        return f"`{kind}/{filename}`"

    new_text = PLUGIN_ROOT_RE.sub(replace, text)

    # Drop disable-model-invocation: true — Codex equivalent goes in openai.yaml.
    fm, body = parse_frontmatter(new_text)
    fm.pop("disable-model-invocation", None)
    new_text = serialize_frontmatter(fm) + body

    skill_md.write_text(new_text)

    # Copy referenced files into the skill's local scripts/ or references/.
    for kind, filename in sorted(referenced):
        src = src_for_ref(kind, filename)
        if not src.exists():
            raise RuntimeError(
                f"{skill_src.name}/SKILL.md references {kind}/{filename}, "
                f"but {src} does not exist."
            )
        dst_dir = skill_out / kind
        dst_dir.mkdir(exist_ok=True)
        dst = dst_dir / filename
        shutil.copyfile(src, dst)
        if kind == "scripts":
            # preserve the executable bit
            os.chmod(dst, os.stat(src).st_mode)

    # Codex's "explicit invocation only" equivalent of disable-model-invocation.
    yaml_dir = skill_out / "agents"
    yaml_dir.mkdir(exist_ok=True)
    (yaml_dir / "openai.yaml").write_text(
        "policy:\n  allow_implicit_invocation: false\n"
    )


# ---------------------------------------------------------------------------
# Agent porting: convert .md → .toml, inline references into developer_instructions

def port_agent(agent_md: Path, out_root: Path) -> None:
    name = agent_md.stem
    out_path = out_root / "agents" / f"{name}.toml"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    text = agent_md.read_text()
    fm, body = parse_frontmatter(text)

    # Inline references: each ${CLAUDE_PLUGIN_ROOT}/... reference is replaced
    # in-prose with a pointer to the inlined section, then the file content is
    # appended below as a "## Reference: <name>" block.
    referenced: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def replace(m: re.Match[str]) -> str:
        kind, filename = m.group(1), m.group(2)
        key = (kind, filename)
        if key not in seen:
            seen.add(key)
            referenced.append(key)
        # The regex consumed any surrounding markdown backticks, so the
        # replacement is plain prose with only the filename in backticks.
        return f"the `{filename}` reference embedded below"

    new_body = PLUGIN_ROOT_RE.sub(replace, body)

    for kind, filename in referenced:
        src = src_for_ref(kind, filename)
        if not src.exists():
            raise RuntimeError(
                f"agents/{name}.md references {kind}/{filename}, "
                f"but {src} does not exist."
            )
        content = src.read_text().rstrip()
        new_body = new_body.rstrip() + f"\n\n## Reference: {filename}\n\n{content}\n"

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
    # ignore_errors lets us survive filesystems (e.g., some FUSE mounts) that
    # refuse unlink; later copytree(dirs_exist_ok=True) and write_text() will
    # overwrite remaining files in place.
    if out_root.exists():
        shutil.rmtree(out_root, ignore_errors=True)
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "skills").mkdir(exist_ok=True)
    (out_root / "agents").mkdir(exist_ok=True)

    if SKILLS_SRC.is_dir():
        for skill_dir in sorted(p for p in SKILLS_SRC.iterdir() if p.is_dir()):
            port_skill(skill_dir, out_root)

    if AGENTS_SRC.is_dir():
        for agent_md in sorted(AGENTS_SRC.glob("*.md")):
            port_agent(agent_md, out_root)


# ---------------------------------------------------------------------------
# --check mode: byte-identical comparison against the committed tree

def trees_equal(a: Path, b: Path) -> tuple[bool, list[str]]:
    """Return (equal, list_of_differences)."""
    diffs: list[str] = []
    _diff_walk(a, b, diffs)
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
