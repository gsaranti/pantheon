#!/usr/bin/env bash
#
# .metis/scripts/build-spec-preflight.sh
#
# Mechanical preflight for /metis-build-spec. Reports input availability
# so the skill can determine the project shape (docs-first / prompt-seeded
# / existing-codebase) and route accordingly.
#
# Output: key=value lines on stdout.
# Exits non-zero if .metis/BUILD.md already exists (this command does not
# edit an existing brief — delete .metis/BUILD.md manually if a fresh
# rewrite is intended).
#
# Fields emitted:
#   DOCS_PRESENT      yes | no    (docs/ has at least one source file)
#   RECONCILE_DONE    yes | no    (.metis/SYNTHESIS.md exists)
#   WALK_PENDING      yes | no    (open or stale items remain)

set -euo pipefail

PROJECT_ROOT="${PWD}"

if [[ -f ".metis/BUILD.md" ]]; then
  printf 'error: .metis/BUILD.md already exists at %s/.metis/BUILD.md — /metis-build-spec only creates the initial brief. Delete .metis/BUILD.md manually if a fresh rewrite is intended.\n' "$(pwd)" >&2
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

DOCS_DIR="docs"
DOCS_PRESENT=no
RECONCILE_DONE=no
WALK_PENDING=no

if [[ -d "$DOCS_DIR" ]]; then
  # All files under docs/ are source material — reconcile outputs live in .metis/
  source_count=0
  while IFS= read -r -d '' _ ; do
    source_count=$(( source_count + 1 ))
  done < <(find "$DOCS_DIR" -type f -print0)

  [[ $source_count -gt 0 ]] && DOCS_PRESENT=yes
fi

[[ -f ".metis/SYNTHESIS.md" ]] && RECONCILE_DONE=yes

pending=$((
  $(count_status ".metis/CONTRADICTIONS.md" open) +
  $(count_status ".metis/QUESTIONS.md" open) +
  $(count_status ".metis/CONTRADICTIONS.md" stale) +
  $(count_status ".metis/QUESTIONS.md" stale)
))
[[ $pending -gt 0 ]] && WALK_PENDING=yes

cat <<EOF
DOCS_PRESENT=$DOCS_PRESENT
RECONCILE_DONE=$RECONCILE_DONE
WALK_PENDING=$WALK_PENDING
EOF
