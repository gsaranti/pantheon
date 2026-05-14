---
name: iris-sync
description: Summarize what the user and Codex have been working on. Reads the Codex chat log from disk and returns a brief synthesis of the current state, recent work, and open threads. Use when you need context on what Codex is doing or has done.
disable-model-invocation: true
context: fork
agent: Explore
allowed-tools: Read
---

# Iris Sync

You are reading a record of a conversation between a user and Codex (a different AI coding assistant). Your job is to help the user's main Claude Code session understand what's been happening on the Codex side.

## Codex chat log

!`cat "${CLAUDE_PROJECT_DIR}/iris-codex-chat.md" 2>/dev/null || echo "[iris-codex-chat.md not found — Codex hasn't written any chat history to this project yet, or the Iris plugin isn't installed on the Codex side.]"`

## Your task

Read the chat log above and produce a brief synthesis covering:

1. **What they're working on.** The current task, feature, or problem in one sentence.
2. **Recent progress.** What has Codex done or attempted in the last few turns.
3. **Open threads.** Anything unresolved, blocked, or explicitly deferred.
4. **The user's apparent intent.** Where the user seems to be heading next, if it's clear from the conversation.

Keep the entire summary to 2–4 sentences. Do not quote the log verbatim. Do not speculate beyond what the log shows. If the log is empty or missing, say so plainly and stop.

Return the summary directly. The main Claude Code session will present it to the user.