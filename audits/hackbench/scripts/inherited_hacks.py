"""Find gold hacks that a record inherits from a shared base trajectory but does not label.

Several records are edits of the same base trajectory. When one record labels a
command as a hack, the identical command in a sibling record (same base, same
text) is the same action and should carry the same label. This script reports,
for every record, the sibling-labelled commands it contains but leaves out of
its own gold set.

usage: python3 -I inherited_hacks.py <hackbench.jsonl>
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import family, load, split_commands


def norm(s):
    return " ".join(s.split())


def main(path):
    rows = load(path)
    blocks = [split_commands(r["monitor_input"]["transcript"]) for r in rows]
    texts = [{k: norm(v) for k, v in b.items()} for b in blocks]
    # labelled-hack command texts, with the records that label them
    labelled = collections.defaultdict(set)
    for i, r in enumerate(rows):
        for g in r["gold_command_indices"]:
            labelled[texts[i][g]].add(i)
    affected = []
    for i, r in enumerate(rows):
        gold = set(r["gold_command_indices"])
        missing = []
        for k, t in texts[i].items():
            if k in gold or len(t) < 40:  # skip trivially short commands (cd, ls)
                continue
            others = labelled.get(t, set()) - {i}
            if others:
                missing.append((k, sorted(others)))
        if missing:
            affected.append((i, missing))
    by_fam = collections.Counter(family(rows[i]) for i, _ in affected)
    print(f"records containing a sibling-labelled hack they do not label: {len(affected)} of {len(rows)}")
    print("by family:", dict(by_fam))
    for i, missing in affected:
        r = rows[i]
        print(f"  #{i:3d} {r['id'][:70]:70s} gold={len(r['gold_command_indices']):3d} "
              f"unlabelled={len(missing)} e.g. CMD {missing[0][0]} (labelled in #{missing[0][1][0]})")


if __name__ == "__main__":
    main(sys.argv[1])
