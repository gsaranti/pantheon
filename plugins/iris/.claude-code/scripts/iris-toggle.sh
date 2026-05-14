#!/bin/bash
set -euo pipefail

# Iris: toggle conversation capture on/off via .iris-config.yaml.
# Called by /iris-on and /iris-off skills with a single arg: "true" or "false".

NEW_VALUE="${1:-}"
if [ "$NEW_VALUE" != "true" ] && [ "$NEW_VALUE" != "false" ]; then
  echo "iris-toggle: expected 'true' or 'false', got '$NEW_VALUE'" >&2
  exit 1
fi

# Resolve project dir — Claude Code sets CLAUDE_PROJECT_DIR; otherwise use cwd.
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
CONFIG="${PROJECT_DIR}/.iris-config.yaml"

if [ ! -f "$CONFIG" ]; then
  cat > "$CONFIG" <<EOF
# Iris configuration. See https://github.com/gsaranti/pantheon/tree/main/plugins/iris.
is_on: $NEW_VALUE
EOF
  echo "iris-toggle: created $CONFIG with is_on: $NEW_VALUE"
  exit 0
fi

# Update an existing is_on line, or append if missing.
if grep -qE '^[[:space:]]*is_on:' "$CONFIG"; then
  # macOS-compatible in-place sed (uses .bak suffix then removes it)
  sed -i.bak -E "s/^[[:space:]]*is_on:.*/is_on: $NEW_VALUE/" "$CONFIG"
  rm -f "${CONFIG}.bak"
else
  printf '\nis_on: %s\n' "$NEW_VALUE" >> "$CONFIG"
fi

echo "iris-toggle: set is_on: $NEW_VALUE in $CONFIG"
