#!/usr/bin/env bash
#
# .metis/scripts/init.sh
#
# Project-specific finalization for Metis. Invoked by /metis-init or directly
# from the shell.
#
# What it does:
#   - Create .metis/ if absent
#   - Populate .metis/config.yaml with name + metis_version + created
#   - Splice the delimited block into CLAUDE.md and AGENTS.md (body from
#     claude-block.md). Both files get the same Metis-managed block but stay
#     independent — runtime-specific content outside the markers is preserved.
#   - Write a .metis/CURRENT.md stub if absent
#
# Idempotent. Re-runs preserve a populated config.yaml unless --reinit is
# passed, and only ever touch content between the delimited markers.
#
# Interactive behavior is gated on stdin being a tty:
#   - tty + no --name      -> prompts for project name (default: dir basename)
#   - non-tty + no --name  -> uses the dir basename silently
#
# Usage:
#   .metis/scripts/init.sh [--name=<name>] [--reinit]

set -euo pipefail

# -- locate plugin root and project root --------------------------------------

# PLUGIN_ROOT is the install directory of the Metis plugin (where this script
# ships); PROJECT_ROOT is the user's project (where init writes outputs). When
# Claude Code invokes this script, $PWD is the user's project.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PROJECT_ROOT="${PWD}"
cd "$PROJECT_ROOT"

# -- arguments ----------------------------------------------------------------

NAME_ARG=""
REINIT=0

for arg in "$@"; do
  case "$arg" in
    --name=*) NAME_ARG="${arg#--name=}" ;;
    --reinit) REINIT=1 ;;
    --help|-h)
      cat <<'USAGE'
Usage: .metis/scripts/init.sh [--name=<name>] [--reinit]

Options:
  --name=<name>   Set project name without prompting.
  --reinit        Re-populate .metis/config.yaml even if already set.
                  (The CLAUDE.md block is always re-applied on every run;
                  this flag only affects config.yaml.)
  -h, --help      Show this message.
USAGE
      exit 0
      ;;
    *)
      printf 'error: unknown argument: %s\n' "$arg" >&2
      exit 2
      ;;
  esac
done

# -- helpers ------------------------------------------------------------------

log() { printf '%s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

prompt_for_name() {
  # Prompt only if stdin is a tty. Otherwise echo the default silently.
  local default="$1"
  local reply=""
  if [[ -t 0 ]]; then
    read -r -p "Project name [${default}]: " reply
    printf '%s' "${reply:-$default}"
  else
    printf '%s' "$default"
  fi
}

# Replace the body between two markers in a file. Markers themselves are
# preserved. If the file doesn't exist, create it containing just the block.
# If the markers aren't present, append the block (with a leading blank line
# when the file already has content).
# Usage: splice_block <file> <start-marker> <end-marker> <body-file>
splice_block() {
  local file="$1" start="$2" end="$3" body_file="$4"

  if [[ ! -f "$body_file" ]]; then
    die "body file not found: $body_file"
  fi

  if [[ ! -f "$file" ]]; then
    {
      printf '%s\n' "$start"
      cat "$body_file"
      printf '%s\n' "$end"
    } > "$file"
    return
  fi

  if grep -qF -- "$start" "$file" && grep -qF -- "$end" "$file"; then
    awk -v s="$start" -v e="$end" -v bf="$body_file" '
      function print_body(   line) {
        while ((getline line < bf) > 0) print line
        close(bf)
      }
      BEGIN { skipping = 0 }
      $0 == s {
        print
        print_body()
        skipping = 1
        next
      }
      $0 == e {
        skipping = 0
        print
        next
      }
      skipping == 0 { print }
    ' "$file" > "${file}.metis.tmp"
    mv "${file}.metis.tmp" "$file"
  else
    if [[ -s "$file" ]]; then
      printf '\n' >> "$file"
    fi
    {
      printf '%s\n' "$start"
      cat "$body_file"
      printf '%s\n' "$end"
    } >> "$file"
  fi
}

# -- sanity checks ------------------------------------------------------------

CLAUDE_BLOCK_FILE="${PLUGIN_ROOT}/.metis/scripts/claude-block.md"
[[ -f "$CLAUDE_BLOCK_FILE" ]] || die "missing block template: $CLAUDE_BLOCK_FILE — Metis plugin install is incomplete."

# Scaffold the project-side .metis/ directory (idempotent).
mkdir -p .metis

# -- decide whether to populate .metis/config.yaml ---------------------------

CONFIG=".metis/config.yaml"
CONFIG_TEMPLATE="${PLUGIN_ROOT}/.metis/config.yaml.template"

existing_name=""
if [[ -f "$CONFIG" ]] && grep -qE '^name:[[:space:]]*\S' "$CONFIG" 2>/dev/null; then
  existing_name="$(awk -F': *' '/^name:/{print $2; exit}' "$CONFIG" | tr -d '\r')"
fi

populate_config=1
if [[ -n "$existing_name" && "$REINIT" -eq 0 ]]; then
  populate_config=0
  log "Metis already initialized (name: ${existing_name}). Re-applying CLAUDE.md and AGENTS.md blocks..."
fi

# -- determine project name ---------------------------------------------------

if [[ -n "$NAME_ARG" ]]; then
  PROJECT_NAME="$NAME_ARG"
elif [[ "$populate_config" -eq 0 ]]; then
  PROJECT_NAME="$existing_name"
else
  default_name="$(basename "$PROJECT_ROOT")"
  PROJECT_NAME="$(prompt_for_name "$default_name")"
  [[ -z "$PROJECT_NAME" ]] && die "No project name supplied."
fi

# -- metis version + today ----------------------------------------------------

VERSION_FILE="${PLUGIN_ROOT}/.metis/version"
[[ -f "$VERSION_FILE" ]] || die "missing $VERSION_FILE — Metis plugin install is incomplete."
METIS_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
[[ -n "$METIS_VERSION" ]] || die "$VERSION_FILE is empty."
TODAY="$(date -u +%Y-%m-%d)"

# -- write .metis/config.yaml (only when populating) --------------------------

if [[ "$populate_config" -eq 1 ]]; then
  [[ -f "$CONFIG_TEMPLATE" && -s "$CONFIG_TEMPLATE" ]] \
    || die "missing or empty $CONFIG_TEMPLATE — Metis distribution is incomplete. Reinstall."
  sed \
    -e "s|{{name}}|${PROJECT_NAME}|g" \
    -e "s|{{metis_version}}|${METIS_VERSION}|g" \
    -e "s|{{today}}|${TODAY}|g" \
    "$CONFIG_TEMPLATE" > "$CONFIG"
  log "Wrote ${CONFIG}."
else
  log "Preserved existing ${CONFIG}."
fi

# -- splice the CLAUDE.md and AGENTS.md blocks -------------------------------

splice_block "CLAUDE.md" "<!-- metis:start -->" "<!-- metis:end -->" "$CLAUDE_BLOCK_FILE"
log "Updated CLAUDE.md (delimited block)."

splice_block "AGENTS.md" "<!-- metis:start -->" "<!-- metis:end -->" "$CLAUDE_BLOCK_FILE"
log "Updated AGENTS.md (delimited block)."

# -- .metis/CURRENT.md stub --------------------------------------------------

if [[ ! -f ".metis/CURRENT.md" ]]; then
  cat > .metis/CURRENT.md <<'EOF'
# Current session handoff

## What happened

*No prior session.*

## Current state

*Nothing in flight.*

## Open questions

*None.*

## Where to start

Run `/metis-session-start` to rehydrate, then pick one of:
- `/metis-reconcile` (docs-first projects)
- `/metis-build-spec "<description>"` (prompt-seeded or existing-codebase)
EOF
  log "Created .metis/CURRENT.md."
fi

# -- summary ------------------------------------------------------------------

cat <<EOF

Metis initialized.

Project:        ${PROJECT_NAME}
Metis version:  ${METIS_VERSION}
Config:         $([ "$populate_config" -eq 1 ] && echo "written" || echo "preserved")

Next step — pick the one that matches your project:
  /metis-reconcile                               # docs-first, greenfield
  /metis-build-spec "<description>"              # prompt-seeded, no docs
  /metis-build-spec "<description of delta>"     # existing codebase
EOF
