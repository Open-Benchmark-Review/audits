#!/bin/sh
# Download the public DeepRSI data that www.deeprsi.com serves to its own front end.
#
# usage: scripts/fetch.sh <out_dir>
#
# Produces:
#   <out_dir>/assets/*.js            front-end bundles (task list, Elo method and ratings are embedded here)
#   <out_dir>/climb.json             task/model/trial metadata parsed from the bundle (no JS is executed)
#   <out_dir>/trials/<id>.json       per-trial record: config, reward breakdown, patch, token/cost metrics
#   <out_dir>/traj/<id>/index.json   trajectory index (truncated messages, block layout)
#   <out_dir>/traj/<id>/block_N.json full trajectory steps
#   <out_dir>/blog.html              methodology blog post
#
# The bundle file names carry content hashes; update BUNDLES if the site is redeployed.
set -eu
OUT=${1:?usage: fetch.sh <out_dir>}
HERE=$(cd "$(dirname "$0")" && pwd)
SITE=https://www.deeprsi.com
BUNDLES="results-oDxM4uUp climb-Cjeh-2Cs elo-intervals-DmHP7iMy trial-C8xV5hYk"
mkdir -p "$OUT/assets" "$OUT/trials" "$OUT/traj"

curl -sSL "$SITE/" -o "$OUT/index.html"
curl -sSL "$SITE/blog/" -o "$OUT/blog.html"
for b in $BUNDLES; do curl -sSL --fail "$SITE/assets/$b.js" -o "$OUT/assets/$b.js"; done

python3 -I "$HERE/parse_bundle.py" "$OUT/assets/climb-Cjeh-2Cs.js" 'var e={' "$OUT/climb.json"
python3 -I -c 'import json,sys; print("\n".join(json.load(open(sys.argv[1]))["trial_tasks"]))' \
  "$OUT/climb.json" > "$OUT/trial_ids.txt"

fetch_trial() {
  id=$1
  [ -s "$OUT/trials/$id.json" ] || curl -sS --fail "$SITE/data/trial-viewer/$id.jgz" | gunzip -c > "$OUT/trials/$id.json"
  d="$OUT/traj/$id"; mkdir -p "$d"
  [ -s "$d/index.json" ] || curl -sS --fail "$SITE/data/trajectory-index/$id.jgz" | gunzip -c > "$d/index.json"
  n=$(python3 -I -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["block_starts"]))' "$d/index.json")
  i=0
  while [ "$i" -lt "$n" ]; do
    [ -s "$d/block_$i.json" ] || curl -sS --fail "$SITE/data/trajectory-steps/$id/$i.jgz" | gunzip -c > "$d/block_$i.json"
    i=$((i + 1))
  done
}

while read -r id; do
  fetch_trial "$id" || echo "FAIL $id" >&2
done < "$OUT/trial_ids.txt"
