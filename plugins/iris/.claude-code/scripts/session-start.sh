#!/bin/bash
set -euo pipefail

# Iris: verify environment and mark session start in the chat log.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
CHAT_FILE="${PROJECT_DIR}/iris-claude-code-chat.md"

# Read the JSON payload (we only need source and session_id)
INPUT="$(cat)"
SOURCE="$(printf '%s' "$INPUT" | jq -r '.source // "unknown"' 2>/dev/null || echo "unknown")"
SESSION_ID="$(printf '%s' "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null || echo "unknown")"

# Check for jq (the chat-append script depends on it).
if ! command -v jq >/dev/null 2>&1; then
  echo "iris: jq is not installed. Install it (brew install jq / apt install jq) for the Iris plugin to capture chat history." >&2
  # Don't exit 2 — that would block the session. Just warn and continue.
fi

# Write a session-start marker so the chat log shows boundaries between sessions.
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
{
  printf '\n---\n## iris session-start (%s)\n\n' "$TIMESTAMP"
  printf 'source: %s\n' "$SOURCE"
  printf 'session_id: %s\n' "$SESSION_ID"
} >> "$CHAT_FILE"

exit 0
