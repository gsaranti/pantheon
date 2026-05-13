#!/usr/bin/env bash
#
# .metis/scripts/walk-open-items-preflight.sh
#
# Mechanical preflight for /metis-walk-open-items. Reports the state of
# captured items so the skill can plan the walk.
#
# Output: key=value lines on stdout.
# Exits non-zero if docs/ is missing or if neither .metis/CONTRADICTIONS.md
# nor .metis/QUESTIONS.md exists (skill surfaces the error and points the
# user at /metis-reconcile).
#
# Fields emitted:
#   OPEN                   total open items across both active files
#   OPEN_CONTRADICTIONS    open items in .metis/CONTRADICTIONS.md
#   OPEN_QUESTIONS         open items in .metis/QUESTIONS.md
#   DEFERRED               total deferred items across both files
#   STALE                  total stale items across both files
#   RESOLVED_PRIOR         items archived in .metis/RESOLVED.md from prior sessions

set -euo pipefail

PROJECT_ROOT="${PWD}"

DOCS_DIR="docs"
[[ -d "$DOCS_DIR" ]] || {
  printf 'error: docs/ not found at %s\n' "$(pwd)" >&2
  exit 1
}

CONTRADICTIONS=".metis/CONTRADICTIONS.md"
QUESTIONS=".metis/QUESTIONS.md"
RESOLVED=".metis/RESOLVED.md"

if [[ ! -f "$CONTRADICTIONS" && ! -f "$QUESTIONS" ]]; then
  printf 'error: no CONTRADICTIONS.md or QUESTIONS.md in .metis/ — run /metis-reconcile first\n' >&2
  exit 1
fi

# Inline helper: print count of "^Status: <value>" lines in <file>.
# Prints 0 if file absent.
count_status() {
  local file="$1" value="$2" n
  [[ -f "$file" ]] || { printf '0'; return; }
  n=$(grep -c "^Status: ${value}" "$file" 2>/dev/null) || n=0
  printf '%d' "$n"
}

OPEN_CONTRADICTIONS=$(count_status "$CONTRADICTIONS" open)
OPEN_QUESTIONS=$(count_status "$QUESTIONS" open)
OPEN=$(( OPEN_CONTRADICTIONS + OPEN_QUESTIONS ))

DEFERRED=$((
  $(count_status "$CONTRADICTIONS" deferred) +
  $(count_status "$QUESTIONS" deferred)
))

STALE=$((
  $(count_status "$CONTRADICTIONS" stale) +
  $(count_status "$QUESTIONS" stale)
))

# RESOLVED.md entries are top-level "## " headings (one per resolved item)
RESOLVED_PRIOR=0
if [[ -f "$RESOLVED" ]]; then
  RESOLVED_PRIOR=$(grep -c '^## ' "$RESOLVED" 2>/dev/null) || RESOLVED_PRIOR=0
fi

cat <<EOF
OPEN=$OPEN
OPEN_CONTRADICTIONS=$OPEN_CONTRADICTIONS
OPEN_QUESTIONS=$OPEN_QUESTIONS
DEFERRED=$DEFERRED
STALE=$STALE
RESOLVED_PRIOR=$RESOLVED_PRIOR
EOF
