#!/bin/bash
set -euo pipefail

# Iris: append user/assistant turns to the rolling chat log
# and overwrite the last-response file on each assistant turn.

ROLE="${1:-}"
if [ "$ROLE" != "user" ] && [ "$ROLE" != "assistant" ]; then
  echo "iris: invalid role '$ROLE' (expected 'user' or 'assistant')" >&2
  exit 0  # non-blocking; we don't want to break Codex
fi

# Read the JSON payload from stdin
INPUT="$(cat)"

# Resolve project dir from the hook payload (.cwd), falling back to $PWD.
PROJECT_DIR="$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null || true)"
PROJECT_DIR="${PROJECT_DIR:-$PWD}"
CHAT_FILE="${PROJECT_DIR}/iris-codex-chat.md"
LAST_FILE="${PROJECT_DIR}/iris-codex-last.md"

# Capture is enabled only when .iris-config.yaml exists and contains `is_on: true`.
grep -qE '^[[:space:]]*is_on:[[:space:]]*true[[:space:]]*(#.*)?$' "${PROJECT_DIR}/.iris-config.yaml" 2>/dev/null || exit 0

# Budget
MAX_TOKENS=50000
CHARS_PER_TOKEN=4
MAX_CHARS=$((MAX_TOKENS * CHARS_PER_TOKEN))

# Extract content based on role.
# Codex hook payloads expose the user prompt at .prompt and the assistant's
# last message at .last_assistant_message — no transcript parsing required.
if [ "$ROLE" = "user" ]; then
  CONTENT="$(printf '%s' "$INPUT" | jq -r '.prompt // empty')"
else
  CONTENT="$(printf '%s' "$INPUT" | jq -r '.last_assistant_message // empty')"
fi

# Skip empty content silently (e.g. tool-only turns)
if [ -z "${CONTENT// }" ]; then
  exit 0
fi

# Overwrite last-response on assistant turns
if [ "$ROLE" = "assistant" ]; then
  printf '%s\n' "$CONTENT" > "$LAST_FILE"
fi

# Append to rolling chat log
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
{
  printf '\n---\n## %s (%s)\n\n' "$ROLE" "$TIMESTAMP"
  printf '%s\n' "$CONTENT"
} >> "$CHAT_FILE"

# Prune from the head if oversized
if [ -f "$CHAT_FILE" ]; then
  CHAT_SIZE="$(wc -c < "$CHAT_FILE")"
  if [ "$CHAT_SIZE" -gt "$MAX_CHARS" ]; then
    KEEP_CHARS=$((MAX_CHARS * 8 / 10))
    # Keep the tail, then snap to the next message boundary so we don't start mid-message
    TAIL_CONTENT="$(tail -c "$KEEP_CHARS" "$CHAT_FILE")"
    CLEAN="$(printf '%s' "$TAIL_CONTENT" | awk '/^---$/{found=1} found' )"
    if [ -z "$CLEAN" ]; then
      # No boundary found in the tail; fall back to the raw tail
      CLEAN="$TAIL_CONTENT"
    fi
    {
      printf '[iris: chat history truncated]\n'
      printf '%s\n' "$CLEAN"
    } > "$CHAT_FILE"
  fi
fi

exit 0
