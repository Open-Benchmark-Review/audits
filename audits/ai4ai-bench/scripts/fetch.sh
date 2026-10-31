#!/bin/sh
# Download the public AI4AI-Bench material used in this audit.
#
# usage: scripts/fetch.sh <out_dir>
#
#   <out_dir>/repo/                    Einsia/AI4AI-Bench at the audited commit (task code, evaluators, orchestrator)
#   <out_dir>/site/cases/<case>.html   the 290 case pages at lab.einsia.ai/ai4ai/trajectories/<case>/
#   <out_dir>/parsed/                  parse_cases.py output (cases.json, cases.csv, text/)
#   <out_dir>/parsed/cells.json        score.py output (sigma per cell)
set -eu
OUT=${1:?usage: fetch.sh <out_dir>}
HERE=$(cd "$(dirname "$0")" && pwd)
COMMIT=5ced1e2eb1882baf52e6d928f9257006aa71968c
SITE=https://lab.einsia.ai/ai4ai
mkdir -p "$OUT/site/cases"

if [ ! -d "$OUT/repo/.git" ]; then
  GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/Einsia/AI4AI-Bench "$OUT/repo"
fi
git -C "$OUT/repo" checkout -q "$COMMIT"

curl -sSL --fail "$SITE/trajectories/" -o "$OUT/site/trajectories.html"
grep -oE 'href="/ai4ai/trajectories/[^"?]+/"' "$OUT/site/trajectories.html" \
  | sed 's#href="/ai4ai/trajectories/##; s#/"##' | sort -u > "$OUT/site/case_ids.txt"
xargs -P 6 -I{} sh -c '[ -s "$1/site/cases/$2.html" ] || curl -sS --fail --retry 3 "$3/trajectories/$2/" -o "$1/site/cases/$2.html"' \
  _ "$OUT" {} "$SITE" < "$OUT/site/case_ids.txt"

python3 -I "$HERE/parse_cases.py" "$OUT/site/cases" "$OUT/parsed"
python3 -I "$HERE/score.py" "$OUT/parsed/cases.json" > "$HERE/../data/rescoring.md"
python3 -I "$HERE/ranking.py" "$OUT/parsed/cells.json" "$HERE/../data/task_reviews" > "$HERE/../data/ranking.md"
