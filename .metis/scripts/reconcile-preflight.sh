#!/usr/bin/env bash
#
# .metis/scripts/reconcile-preflight.sh
#
# Mechanical preflight for /metis-reconcile. Reports the shape of the
# docs/ corpus so the skill can plan its read.
#
# Output: key=value lines on stdout. Exits non-zero if docs/ is missing.
#
# Fields emitted:
#   STATUS                fresh | rereconcile
#   DOCS_COUNT            number of source files under docs/
#   CORPUS_WORDS          sum of wc -w across source files
#   CORPUS_TOKENS_EST     tokens estimate (words × per-file-type multiplier)
#   SIZE_CLASS            small (<40k) | medium (40-80k) | large (>=80k)
#   PRIOR_OPEN            open items carried in CONTRADICTIONS.md + QUESTIONS.md
#   PRIOR_DEFERRED        deferred items carried forward
#   PRIOR_STALE           stale items carried forward
#
# PRIOR_* are always 0 when STATUS=fresh.

set -euo pipefail

PROJECT_ROOT="${PWD}"

DOCS_DIR="docs"
[[ -d "$DOCS_DIR" ]] || {
  printf 'error: docs/ not found at %s\n' "$(pwd)" >&2
  exit 1
}

# Inline helper: print count of "^Status: <value>" lines in <file>.
# Prints 0 if file absent.
count_status() {
  local file="$1" value="$2" n
  [[ -f "$file" ]] || { printf '0'; return; }
  n=$(grep -c "^Status: ${value}" "$file" 2>/dev/null) || n=0
  printf '%d' "$n"
}

# -- enumerate source docs ---------------------------------------------------
# All files under docs/ are source material — reconcile outputs live in .metis/
# so there's nothing to exclude.

source_files=()
while IFS= read -r -d '' f; do
  source_files+=("$f")
done < <(find "$DOCS_DIR" -type f -print0)

DOCS_COUNT=${#source_files[@]}

# -- word count + token estimate (per-file-type multiplier, integer math) ----

# Multipliers scaled ×10 to avoid floating point:
#   prose (.md .txt .rst)                          -> 13   (×1.3)
#   schema (.yaml .yml .json .toml .xml .csv)      -> 18   (×1.8)
#   code   (.py .js .ts .go .rb .rs .java .c etc.) -> 15   (×1.5)
#   other                                           -> 13   (default, treat as prose)

total_words=0
total_tokens_est=0
for f in "${source_files[@]}"; do
  w=$(wc -w < "$f" 2>/dev/null | tr -d ' ')
  [[ -z "$w" ]] && w=0
  ext="${f##*.}"
  case "$ext" in
    yaml|yml|json|toml|xml|csv)              mult=18 ;;
    py|js|ts|go|rb|rs|java|c|cpp|h|hpp)      mult=15 ;;
    *)                                        mult=13 ;;
  esac
  tokens=$(( (w * mult) / 10 ))
  total_words=$(( total_words + w ))
  total_tokens_est=$(( total_tokens_est + tokens ))
done

# -- classify corpus size ----------------------------------------------------

if   (( total_tokens_est < 40000 )); then SIZE_CLASS=small
elif (( total_tokens_est < 80000 )); then SIZE_CLASS=medium
else                                      SIZE_CLASS=large
fi

# -- fresh vs rereconcile ----------------------------------------------------

STATUS=fresh
for out in SYNTHESIS.md INDEX.md CONTRADICTIONS.md QUESTIONS.md; do
  if [[ -f ".metis/$out" ]]; then
    STATUS=rereconcile
    break
  fi
done

# -- prior item counts (rereconcile only) ------------------------------------

PRIOR_OPEN=0
PRIOR_DEFERRED=0
PRIOR_STALE=0

for f in ".metis/CONTRADICTIONS.md" ".metis/QUESTIONS.md"; do
  PRIOR_OPEN=$((     PRIOR_OPEN     + $(count_status "$f" open) ))
  PRIOR_DEFERRED=$(( PRIOR_DEFERRED + $(count_status "$f" deferred) ))
  PRIOR_STALE=$((    PRIOR_STALE    + $(count_status "$f" stale) ))
done

# -- pre-create stubs (after STATUS detection so it's not poisoned) ----------
#
# Stubs exist so the skill can use Edit on the first run rather than emitting
# heading-level boilerplate as Write output. STATUS was set above based on
# pre-stub existence, so a fresh project that has never run reconcile will
# correctly read STATUS=fresh even after these stubs are written.

mkdir -p .metis

if [[ ! -f .metis/SYNTHESIS.md ]]; then
  cat > .metis/SYNTHESIS.md <<'EOF'
# Synthesis

*One-page own-words summary of what is being built. Written by /metis-reconcile.*

(reconcile has not run yet)
EOF
fi

if [[ ! -f .metis/INDEX.md ]]; then
  cat > .metis/INDEX.md <<'EOF'
# Index

*Concept → file:section map. Written by /metis-reconcile.*

(no entries yet)
EOF
fi

if [[ ! -f .metis/CONTRADICTIONS.md ]]; then
  cat > .metis/CONTRADICTIONS.md <<'EOF'
# Contradictions

*Open and deferred items, one `##` heading per item. Resolved items move to `RESOLVED.md`.*

(no items yet)
EOF
fi

if [[ ! -f .metis/QUESTIONS.md ]]; then
  cat > .metis/QUESTIONS.md <<'EOF'
# Questions

*Open and deferred items, one `##` heading per item. Resolved items move to `RESOLVED.md`.*

(no items yet)
EOF
fi

# -- emit report -------------------------------------------------------------

cat <<EOF
STATUS=$STATUS
DOCS_COUNT=$DOCS_COUNT
CORPUS_WORDS=$total_words
CORPUS_TOKENS_EST=$total_tokens_est
SIZE_CLASS=$SIZE_CLASS
PRIOR_OPEN=$PRIOR_OPEN
PRIOR_DEFERRED=$PRIOR_DEFERRED
PRIOR_STALE=$PRIOR_STALE
EOF
