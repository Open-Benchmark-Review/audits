"""Diff each record against its siblings built from the same base trajectory.

For records that share a base trajectory, the commands that differ between them
are exactly what was injected. This reports, per record, which command indices
are unique to it and whether its gold set lies inside them. A gold command that
also appears verbatim in a sibling was not injected into this record.

usage: python3 -I sibling_diff.py <hackbench.jsonl>
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import family, load, split_commands


def norm(s):
    return " ".join(s.split())


def clusters(texts):
    n = len(texts)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    sets = [set(t.values()) for t in texts]
    for i in range(n):
        for j in range(i + 1, n):
            a, b = sets[i], sets[j]
            if len(a & b) / max(1, min(len(a), len(b))) > 0.8:
                parent[find(i)] = find(j)
    groups = collections.defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)
    return [g for g in groups.values() if len(g) > 1]


def main(path):
    rows = load(path)
    texts = [{k: norm(v) for k, v in split_commands(r["monitor_input"]["transcript"]).items()} for r in rows]
    stats = collections.Counter()
    print("record  family                    cmds unique gold gold_in_unique  id")
    for group in clusters(texts):
        for i in group:
            others = set().union(*(set(texts[j].values()) for j in group if j != i))
            unique = {k for k, t in texts[i].items() if t not in others}
            gold = set(rows[i]["gold_command_indices"])
            inside = len(gold & unique)
            stats["records"] += 1
            stats["gold"] += len(gold)
            stats["gold_in_unique"] += inside
            stats["unique_equals_gold"] += unique == gold
            stats["gold_subset_unique"] += gold <= unique
            print(f"#{i:<6d} {family(rows[i]):25s} {len(texts[i]):4d} {len(unique):6d} {len(gold):4d} {inside:14d}  {rows[i]['id'][:60]}")
    print(dict(stats))


if __name__ == "__main__":
    main(sys.argv[1])
