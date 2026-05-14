#!/bin/bash
set -euo pipefail

# Iris: append user/assistant turns to the rolling chat log
# and overwrite the last-response file on each assistant turn.

ROLE="${1:-}"
if [ "$ROLE" != "user" ] && [ "$ROLE" != "assistant" ]; then
  echo "iris: invalid role '$ROLE' (expected 'user' or 'assistant')" >&2
  exit 0  # non-blocking; we don't want to break Claude Code
fi

# Project files
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
CHAT_FILE="${PROJECT_DIR}/iris-claude-code-chat.md"
LAST_FILE="${PROJECT_DIR}/iris-claude-code-last.md"

# Budget
MAX_TOKENS=50000
CHARS_PER_TOKEN=4
MAX_CHARS=$((MAX_TOKENS * CHARS_PER_TOKEN))

# Read the JSON payload from stdin
INPUT="$(cat)"

# Extract content based on role
if [ "$ROLE" = "user" ]; then
  CONTENT="$(printf '%s' "$INPUT" | jq -r '.prompt // empty')"
else
  TRANSCRIPT="$(printf '%s' "$INPUT" | jq -r '.transcript_path // empty')"
  if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then
    exit 0
  fi
  # Pull the last assistant message's text content from the JSONL transcript
  CONTENT="$(
    tac "$TRANSCRIPT" 2>/dev/null \
      | awk '
          BEGIN { found=0 }
          {
            # Find the most recent assistant message line
            if (!found && index($0, "\"type\":\"assistant\"")) {
              print $0
              found=1
              exit
            }
          }
        ' \
      | jq -r '
          .message.content
          | if type == "array"
            then map(select(.type == "text") | .text) | join("\n")
            else . // empty
            end
        ' 2>/dev/null
  )"
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
