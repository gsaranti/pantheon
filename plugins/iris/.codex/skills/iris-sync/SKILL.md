---
name: iris-sync
description: Summarize what the user and Claude Code have been working on. Reads the Claude Code chat log from disk and returns a brief synthesis of the current state, recent work, and open threads. Use when you need context on what Claude Code is doing or has done.
---

# $iris-sync

You are reading a record of a conversation between a user and Claude Code (a different AI coding assistant). Your job is to help the user's main Codex session understand what's been happening on the Claude Code side.

## Steps

1. Read `iris-claude-code-chat.md` from the project root.
2. If the file is missing or empty, say so plainly and stop. Do not proceed.
3. Produce a brief synthesis covering:
   - **What they're working on** — the current task, feature, or problem in one sentence.
   - **Recent progress** — what Claude Code has done or attempted in the last few turns.
   - **Open threads** — anything unresolved, blocked, or explicitly deferred.
   - **The user's apparent intent** — where the user seems to be heading next, if it's clear from the conversation.

Keep the entire summary to 2–4 sentences. Do not quote the log verbatim. Do not speculate beyond what the log shows.

Return the summary directly. The main Codex session will present it to the user.
