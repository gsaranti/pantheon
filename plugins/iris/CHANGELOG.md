# Changelog

All notable changes to Iris are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/), versioning follows [SemVer](https://semver.org/).

## [0.1.0] — 2026-05-13

Initial release. Iris ships as a matched pair of plugins — one for Claude Code, one for Codex — that act as a thin context bridge between the two. Each side persists its own conversation to disk; the other side reads what was written. The skill set on each side is symmetric: `/iris-sync` summarizes what the other tool has been doing, `/iris-relay` executes its last response as a plan, and `/iris-off` / `/iris-on` toggle whether capture happens at all. Capture is opt-in per project — fresh installs do nothing until you run `/iris-on` once, which writes `is_on: true` to `.iris-config.yaml` at the project root. There is no shared protocol, no coordination layer, no version negotiation — both halves just read the files the other half wrote.

### Added

- **Claude Code plugin** at `.claude-code/`. Three hooks capture the conversation: `SessionStart` writes a session marker, `UserPromptSubmit` appends the user turn, and `Stop` appends the assistant turn (parsed from the JSONL session transcript) and overwrites the last-response file. Output goes to `iris-claude-code-chat.md` (rolling, capped at ~50k tokens, head-pruned with message-boundary snapping when the cap is hit) and `iris-claude-code-last.md` (overwritten every assistant turn). Hook scripts run via `${CLAUDE_PLUGIN_ROOT}` and are zero-cost at the model layer — the content was already generated, the hook just persists it.
- **Four Claude Code skills**, all with `disable-model-invocation: true` so Claude Code never fires them automatically:
  - `/iris-sync` — runs in a forked Explore subagent (`context: fork`, `agent: Explore`, `allowed-tools: Read`) against `iris-codex-chat.md`, returns a 2–4 sentence synthesis of what Codex and the user have been working on. The fork keeps the chat-log content out of the main session's context.
  - `/iris-relay` — reads `iris-codex-last.md` and treats its content as a plan to implement, with explicit framing that the file is data (not trusted instructions). Stops to ask before doing anything destructive or ambiguous.
  - `/iris-on` / `/iris-off` — call `scripts/iris-toggle.sh` to set `is_on: true | false` in `.iris-config.yaml` at the project root. `allowed-tools: Bash` restricts each skill to running the single toggle command and nothing else.
- **Codex plugin** at `.codex/`. Mirror of the Claude Code side: `SessionStart` / `UserPromptSubmit` / `Stop` hooks write to `iris-codex-chat.md` and `iris-codex-last.md`; four skills (`$iris-sync`, `$iris-relay`, `$iris-off`, `$iris-on`) parallel the Claude Code set. Hook commands use `${PLUGIN_ROOT}` for plugin-root resolution; the `Stop` hook reads `last_assistant_message` from the payload directly (Codex exposes it inline — no transcript parsing required, unlike Claude Code's `tac`/`awk`/`jq` over the JSONL transcript). Skill invocation policy moves to `agents/openai.yaml` as `policy.allow_implicit_invocation: false` (Codex's equivalent of `disable-model-invocation: true`). Codex skills can only reach files inside their own directory, so each toggle skill ships its own copy of `iris-toggle.sh` under `references/`.
- **Capture toggle.** A small bash script (`scripts/iris-toggle.sh` on Claude Code, each toggle skill's `references/iris-toggle.sh` on Codex) writes `is_on: true | false` to `.iris-config.yaml` at the project root, creating the file if it doesn't exist and preserving any other fields if it does. The hooks check that file with an anchored grep at the top of each invocation and exit silently unless they see exactly `is_on: true`. **Capture is opt-in per project** — fresh installs have no config file, so the hooks do nothing until `/iris-on` is run once. This is deliberate: Iris persists conversation content to disk, and a per-project opt-in keeps that surface visible. The read skills (`/iris-sync`, `/iris-relay`) continue to work while capture is off — they read whatever's already on disk.
- **Marketplace install** for both runtimes from `gsaranti/pantheon`:
  - Claude Code: `/plugin marketplace add gsaranti/pantheon`, then `/plugin install iris@pantheon`.
  - Codex: `codex plugin marketplace add gsaranti/pantheon`, then install from the `/plugins` UI.

### Notes

- Iris pays off when you use both tools on the same project — plan in one, implement in the other, or pick up in the other when one hits a usage limit. Installing only one half is supported (the files the half writes are just inert until the other half reads them), but the bridge isn't useful until both halves are in place.
- `jq` is a runtime dependency on both sides — the hook scripts use it to parse hook payloads (and on Claude Code, to walk the JSONL transcript). `brew install jq` on macOS, `apt install jq` on Linux.
- The Codex side requires both `codex_hooks` and `plugin_hooks` feature flags in `~/.codex/config.toml`; both are still experimental in Codex as of this release.
- Codex `$iris-sync` runs in the main session rather than a forked subagent — Codex skills don't expose context-forking as a frontmatter knob the way Claude Code does. The 50k-token cap on the chat log bounds the worst-case context cost, but the read still lands in the main thread. The Claude Code `/iris-sync` continues to fork.
- Recommended: add `iris-*.md` to your `.gitignore`. The four chat/last files Iris writes are local working state, not project content; gitignoring them keeps PRs clean and prevents conflicts on shared branches. `.iris-config.yaml` is intentionally not covered by that pattern — commit it to share the toggle state with collaborators, leave it untracked for personal control.

[0.1.0]: https://github.com/gsaranti/pantheon/releases/tag/v0.1.0
