#!/usr/bin/env bash
#
# .metis/scripts/review-task-preflight.sh
#
# Mechanical preflight for /metis-review-task. Resolves the baseline branch
# the implementation diverges from, and reports whether the working tree
# or branch has changes to review.
#
# Output: key=value lines on stdout.
# Exits non-zero if the working directory isn't a git repository.
#
# Fields emitted:
#   BASELINE        the first existing branch from the cascade main, master,
#                   origin/main, origin/master. Empty if none of the four exist.
#   DIFF_PRESENT    yes | no — uncommitted changes OR commits ahead of BASELINE.

set -euo pipefail

PROJECT_ROOT="${PWD}"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  printf 'error: not in a git repository — /metis-review-task needs git to scope the review.\n' >&2
  exit 1
fi

# -- resolve baseline --------------------------------------------------------
# The first branch from the cascade that exists. Empty if none do — the
# subagent then falls back to reviewing uncommitted changes only.

BASELINE=""
for candidate in main master origin/main origin/master; do
  if git rev-parse --verify --quiet "$candidate" >/dev/null 2>&1; then
    BASELINE="$candidate"
    break
  fi
done

# -- detect any diff to review ----------------------------------------------
# Presence is the union of (uncommitted changes) and (commits ahead of BASELINE).

DIFF_PRESENT=no
if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
  DIFF_PRESENT=yes
elif [[ -n "$BASELINE" ]]; then
  head_commits=$(git rev-list --count "${BASELINE}..HEAD" 2>/dev/null || echo 0)
  [[ "$head_commits" -gt 0 ]] && DIFF_PRESENT=yes
fi

cat <<EOF
BASELINE=$BASELINE
DIFF_PRESENT=$DIFF_PRESENT
EOF
