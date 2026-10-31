"""Draw the stratified random review sample (Epoch: 50 items when a benchmark has >50).

Strata are construction families (read from record ids); allocation is proportional
with at least one record per family. Seeded so the sample is reproducible.

usage: python3 -I sample.py <hackbench.jsonl> [n=50] [seed=20261027]
"""
import collections
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import family, load


def main(path, n=50, seed=20261027):
    rows = load(path)
    strata = collections.defaultdict(list)
    for i, r in enumerate(rows):
        strata[family(r)].append(i)
    alloc = {f: max(1, round(n * len(v) / len(rows))) for f, v in strata.items()}
    while sum(alloc.values()) > n:
        alloc[max(alloc, key=alloc.get)] -= 1
    while sum(alloc.values()) < n:
        alloc[max(alloc, key=lambda f: len(strata[f]) / alloc[f])] += 1
    rng = random.Random(seed)
    pick = []
    for f in sorted(strata):
        pick += sorted(rng.sample(strata[f], alloc[f]))
        print(f"{f}: {alloc[f]} of {len(strata[f])}", file=sys.stderr)
    print(" ".join(map(str, sorted(pick))))


if __name__ == "__main__":
    main(sys.argv[1], *map(int, sys.argv[2:]))
