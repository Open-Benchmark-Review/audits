#!/bin/sh
# Download the public FrontierML data that www.frontierml.org serves to its own front end.
#
# usage: scripts/fetch.sh <out_dir> [model ...]
#   With no models, fetches the six audited ones. Model ids as on the site, e.g. claude-opus-5-5.
#
# Produces:
#   <out_dir>/site/{data,data_trials,data_tasks,blog}.html   heatmap, trial table, task catalog, methodology post
#   <out_dir>/trials.json            every trial record on /data/trials/ (all 19 models, 1197 trials)
#   <out_dir>/pages/<trial>.html     trial page: score breakdown, reviewer checks, self-check log
#   <out_dir>/trajids.json           trial id -> trajectory id (embedded in the trial page)
#   <out_dir>/traj/<trajid>.json.gz  full trajectory, as served at /trajectories/<trajid>.json
set -eu
OUT=${1:?usage: fetch.sh <out_dir> [model ...]}
shift
MODELS=${*:-claude-opus-5-5 claude-fable-5-1 gpt-6-astra gemini-4-argon muse-wonder deepseek-v4-1-flash}
HERE=$(cd "$(dirname "$0")" && pwd)
SITE=https://www.frontierml.org
mkdir -p "$OUT/site" "$OUT/pages" "$OUT/traj"

curl -sSL --fail "$SITE/data/" -o "$OUT/site/data.html"
curl -sSL --fail "$SITE/data/trials/" -o "$OUT/site/data_trials.html"
curl -sSL --fail "$SITE/data/tasks/" -o "$OUT/site/data_tasks.html"
curl -sSL --fail "$SITE/blog/" -o "$OUT/site/blog.html"
python3 -I "$HERE/parse_site.py" trials "$OUT/site/data_trials.html" "$OUT/trials.json"

python3 -I -c 'import json,sys; ms=set(sys.argv[2:]); print("\n".join(r["id"] for r in json.load(open(sys.argv[1])) if r["model"] in ms))' \
  "$OUT/trials.json" $MODELS > "$OUT/trial_ids.txt"
xargs -P 8 -I{} sh -c '[ -s "$1/pages/$2.html" ] || curl -sS --fail --retry 3 -o "$1/pages/$2.html" "$3/trials/$2/"' _ "$OUT" {} "$SITE" \
  < "$OUT/trial_ids.txt"

python3 -I "$HERE/parse_site.py" trajids "$OUT/pages" "$OUT/trajids.json"
python3 -I -c 'import json,sys; print("\n".join(v for v in json.load(open(sys.argv[1])).values() if v))' "$OUT/trajids.json" \
  | xargs -P 8 -I{} sh -c '[ -s "$1/traj/$2.json.gz" ] || curl -sS --fail --retry 3 --compressed "$3/trajectories/$2.json" | gzip > "$1/traj/$2.json.gz"' _ "$OUT" {} "$SITE"
echo "$(ls "$OUT/traj" | wc -l) trajectories -> $OUT/traj"
