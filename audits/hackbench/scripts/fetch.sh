#!/bin/sh
# Download the public HackBench release and the blog's figures.
#
# usage: HF_TOKEN=... scripts/fetch.sh <out_dir>
#
# The dataset is gated (CC BY-NC 4.0; accept the terms at
# https://huggingface.co/datasets/facebook/hackbench first) and may not be rehosted,
# so this audit commits only derived statistics and short quotes.
#
# Produces:
#   <out_dir>/hf/{README.md,MANIFEST.json,SHA256SUMS,schemas/example.schema.json}
#   <out_dir>/hf/data/hackbench_169_gpt55_glm52.numbered.jsonl   (408,528,473 bytes)
#   <out_dir>/blog/README.md and figures, from facebookresearch/RAM (gh-pages and main)
set -eu
OUT=${1:?usage: fetch.sh <out_dir>}
: "${HF_TOKEN:?set HF_TOKEN to a token whose account accepted the dataset terms}"
HF=https://huggingface.co/datasets/facebook/hackbench/resolve/main
mkdir -p "$OUT/hf/data" "$OUT/hf/schemas" "$OUT/blog"
for f in README.md MANIFEST.json SHA256SUMS schemas/example.schema.json \
         data/hackbench_169_gpt55_glm52.numbered.jsonl; do
  curl -sSL --fail -H "Authorization: Bearer $HF_TOKEN" "$HF/$f" -o "$OUT/hf/$f"
done
(cd "$OUT/hf" && sha256sum -c SHA256SUMS)

# The blog page and its figures. fig3-fig5 are committed next to the post but not shown in it.
GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 https://github.com/facebookresearch/RAM "$OUT/ram"
cp "$OUT/ram/projects/hackbench/"* "$OUT/blog/"
