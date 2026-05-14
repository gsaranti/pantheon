# Iris

> *The messenger between worlds.*

A thin context bridge between Claude Code and Codex. Iris logs your conversation to disk and exposes it to the other tool, so you can hand off plans, share context, and pick up where each tool left off.

Iris doesn't try to be a workflow. It writes plain markdown files at known paths. The tools on either side decide what to do with them.

---

## Contents

- [What Iris is](#what-iris-is)
- [Who it's for](#who-its-for)
- [How it works](#how-it-works)
- [Installation](#installation)
- [The skill set](#the-skill-set)
- [Files Iris writes](#files-iris-writes)
- [Principles](#principles)
- [License & Repository](#license--repository)

---

## What Iris is

Three hooks and four skills. The hooks capture your conversation. Two skills read what the *other* tool captured (`/iris-sync` summarizes, `/iris-relay` executes); two toggle capture on and off for this project (`/iris-off`, `/iris-on`).

What you get on disk, in your project root:

- **`iris-claude-code-chat.md`** — rolling log of the conversation between you and Claude Code. Capped at ~50k tokens; oldest content drops when the cap is hit.
- **`iris-claude-code-last.md`** — the last response Claude Code produced. Overwritten on every turn.
- **`iris-codex-chat.md`** — Codex's equivalent, written by the Codex side of Iris.
- **`iris-codex-last.md`** — Codex's last response.

What you get as skills: four commands. `/iris-sync` and `/iris-relay` read what the other tool has been doing; `/iris-off` and `/iris-on` toggle capture on this side. Codex addresses them as `$iris-*`.

The Claude Code side reads the Codex files. The Codex side reads the Claude Code files. Each tool writes its own, reads the other's. Symmetric, no shared infrastructure, no API.

---

## Who it's for

Engineers who use both Claude Code and Codex on the same project and want a low-friction way to share context between them without retyping or copy-pasting.

Iris pays off when:

- You plan in one tool and implement in the other.
- You hit a usage limit on one and want the other to pick up.
- You want a second AI's read on what the first one just did.

Iris is the wrong tool if you only use one of the two. The files Iris writes are inert without a tool on the other side reading them.

---

## How it works

Three hooks fire automatically as you work:

- **`SessionStart`** writes a session-boundary marker into the rolling chat log, so the file shows where each session begins.
- **`UserPromptSubmit`** appends your message to the chat log.
- **`Stop`** appends the assistant's response to the chat log and overwrites the last-response file.

All three run locally as shell scripts. They cost zero tokens — the content already exists; Iris just persists it. On Claude Code, the `Stop` hook walks Claude's JSONL session transcript to pull the last assistant message; on Codex, the hook reads it directly off the payload.

The skills are user-invoked:

- **`/iris-sync`** reads the *other* tool's rolling chat log and returns a 2–4 sentence summary of what it and the user have been working on. On Claude Code, this runs in a forked Explore subagent so the chat-log content stays out of the main session's context. On Codex the read happens in the main session — Codex doesn't expose context-forking as a skill knob — but the 50k-token cap on the chat log bounds the worst-case cost.
- **`/iris-relay`** reads the *other* tool's last response and treats it as a plan to implement. Use it when the other tool has produced something — a plan, a refactor outline, a research summary — that you want this tool to execute against.

Each side is symmetric: it writes `iris-<itself>-*.md` and reads `iris-<other>-*.md`.

Two more skills control whether capture happens at all. **`/iris-on`** sets `is_on: true` in `.iris-config.yaml` at the project root; **`/iris-off`** flips it back to `false`. Each hook reads that file at the top of its run and exits silently unless it sees `is_on: true`. The toggle is project-scoped — both halves of Iris check the same file, so one command moves both sides at once. The read skills (`/iris-sync`, `/iris-relay`) keep working while Iris is off; they read whatever's already on disk.

**Capture is opt-in.** Fresh installs don't write the config file, so the hooks no-op until you run `/iris-on` (or `$iris-on`) once per project. This is deliberate — Iris persists conversation content to disk, and a per-project opt-in keeps that surface visible.

---

## Installation

Iris ships as a plugin for both Claude Code and Codex. Install both to get the full bridge.

### Claude Code

```
/plugin marketplace add gsaranti/pantheon
/plugin install iris@pantheon
```

### Codex

Register the Pantheon marketplace from your shell:

```bash
codex plugin marketplace add gsaranti/pantheon
```

Then open Codex, browse to the `pantheon` marketplace in the plugin directory, and install Iris:

```
codex
/plugins
```

#### Codex feature flags

Plugin-bundled hooks on Codex are gated behind two feature flags. Enable both in `~/.codex/config.toml`:

```toml
[features]
codex_hooks = true
plugin_hooks = true
```

Without these, the Codex side of Iris installs cleanly but the hooks never fire — capture silently does nothing, and `$iris-sync` / `$iris-relay` will find empty files.

### First run

After installing, run `/iris-on` (Claude Code) or `$iris-on` (Codex) once per project to start capture. That creates `.iris-config.yaml` with `is_on: true` in the project root; the hooks check that file at the top of each invocation and only fire when they see `is_on: true`. Until then, Iris is installed but silent.

### Requirements

- `jq` installed locally (`brew install jq` on macOS, `apt install jq` on Linux). Iris uses `jq` to parse hook payloads (and on Claude Code, to walk the JSONL session transcript).

### A note on syntax

Examples throughout this README use Claude Code's `/iris-*` form. Codex addresses skills with `$` instead — substitute `$iris-sync`, `$iris-relay`, `$iris-off`, or `$iris-on` when invoking from Codex.

### Recommended

Add Iris's artifacts to your `.gitignore`:

```
iris-*.md
```

The files are local working state, not project content. Gitignoring them keeps PRs clean and prevents conflicts on shared branches.

The pattern intentionally excludes `.iris-config.yaml` — that's your project's toggle state, and whether to commit it is a choice (see [Controlling capture](#controlling-capture)).

---

## The skill set

Four skills, all prefixed `/iris-` (or `$iris-` on Codex).

### Reading the other tool

- **`/iris-sync`** — summarize what the other tool has been doing. Reads its rolling chat log; returns a brief synthesis. On Claude Code this runs in a forked Explore subagent; on Codex it runs in the main session.
- **`/iris-relay`** — execute the other tool's last response. Reads its last-response file and treats the content as a plan. Stops to ask if anything is ambiguous before making changes.

### Controlling capture

- **`/iris-on`** — enable Iris's hooks for this project. Calls a small toggle script that writes `is_on: true` to `.iris-config.yaml` in the project root (creating the file if it doesn't exist). Capture starts on the next turn. **Required at least once per project** — fresh installs have no config file and capture is off by default.
- **`/iris-off`** — pause Iris's hooks. Sets `is_on: false` in `.iris-config.yaml`. The hooks see the false value and no-op. Existing chat logs and last-response files are preserved.

`.iris-config.yaml` is project-scoped — both the Claude Code and Codex sides of Iris read the same file, so one command toggles both halves at once. It's not gitignored by default; commit it to share the toggle state with collaborators, leave it untracked for personal control.

All four skills are explicit-invocation only — neither tool fires them automatically. The Claude Code skills set `disable-model-invocation: true`; the Codex skills set `policy.allow_implicit_invocation: false` in `agents/openai.yaml`. You invoke them when you want the handoff or want to flip the switch.

---

## Files Iris writes

All four files live in your project root and follow the same naming convention: `iris-<tool>-<kind>.md`.

| File | Written by | Contents |
|---|---|---|
| `iris-claude-code-chat.md` | Claude Code's Iris | Rolling chat log, capped at ~50k tokens |
| `iris-claude-code-last.md` | Claude Code's Iris | Last Claude Code response, overwritten each turn |
| `iris-codex-chat.md` | Codex's Iris | Rolling chat log from the Codex side |
| `iris-codex-last.md` | Codex's Iris | Last Codex response, overwritten each turn |

Claude Code's Iris writes the first two and reads the last two. Codex's Iris does the reverse. There is no coordination layer — both sides just read what the other wrote.

One additional file lives at the project root: **`.iris-config.yaml`**. It holds a single field — `is_on: true | false` — written by the toggle script when you run `/iris-on` or `/iris-off`. The hooks consult it before doing anything; without it, capture stays off.

---

## Principles

1. **Structure on disk, not in the tools.** Iris writes plain markdown files at known paths. Either tool can read them, the user can read them, future tools can read them. The contract is the file format.

2. **Symmetric, not coordinated.** Each side does its own work without knowing or caring about the other. No shared state, no protocol, no version negotiation. If one side isn't installed, the other side still works — it just sees empty files.

3. **Zero token cost for capture.** Hooks run as local shell scripts. The conversation content was already generated by the model; Iris just persists it. The only token cost is when you invoke `/iris-sync` or `/iris-relay`, and even then it's bounded by the file size cap.

4. **User-driven handoffs.** Iris doesn't auto-sync or auto-execute. You decide when to pull the other tool's context in (`/iris-sync`) and when to act on it (`/iris-relay`). Cross-tool handoff is a judgment call; Iris stays out of it.

5. **Treat cross-tool content as data, not instructions.** When `/iris-relay` reads the other tool's last response, it treats the content as a plan to evaluate, not as authoritative instructions from a trusted source. If the plan looks wrong, Iris stops and asks.

---

## License & Repository

**License**: MIT. See [`LICENSE`](LICENSE).

**Repository**: <https://github.com/gsaranti/pantheon>
