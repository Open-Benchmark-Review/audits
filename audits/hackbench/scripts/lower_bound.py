"""Judgement-free lower bound on defective records over all 169.

A record is counted if any of these mechanical checks fires:
  - sibling-inconsistent gold: it contains, unlabelled, a command whose identical text is gold
    in another record built on the same trajectory (inherited_hacks.py), or it shares a
    byte-identical transcript with a record that has a different gold set;
  - answer leak: the monitor's task context contains the red-team order to hack;
  - its own injected command (sibling diff) is absent from its gold while the gold labels only
    commands shared with siblings.

usage: python3 -I lower_bound.py <hackbench.jsonl>
"""
import collections
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import family, load, split_commands
from sibling_diff import clusters, norm


def main(path):
    rows = load(path)
    texts = [{k: norm(v) for k, v in split_commands(r["monitor_input"]["transcript"]).items()} for r in rows]
    flags = collections.defaultdict(set)
    labelled = collections.defaultdict(set)
    for i, r in enumerate(rows):
        for g in r["gold_command_indices"]:
            labelled[texts[i][g]].add(i)
    for i, r in enumerate(rows):
        gold = set(r["gold_command_indices"])
        if any(len(t) >= 40 and labelled.get(t, set()) - {i} for k, t in texts[i].items() if k not in gold):
            flags[i].add("sibling-inconsistent gold")
        if "red-team agent" in r["monitor_input"]["task_instruction"]:
            flags[i].add("red-team order in monitor input")
    byhash = collections.defaultdict(list)
    for i, r in enumerate(rows):
        byhash[hashlib.sha256(r["monitor_input"]["transcript"].encode()).hexdigest()].append(i)
    for v in byhash.values():
        if len({tuple(sorted(rows[i]["gold_command_indices"])) for i in v}) > 1:
            for i in v:
                flags[i].add("identical transcript, different gold")
    for group in clusters(texts):
        for i in group:
            others = set().union(*(set(texts[j].values()) for j in group if j != i))
            uniq = {k for k, t in texts[i].items() if t not in others}
            if len(uniq) == 1 and not (uniq & set(rows[i]["gold_command_indices"])):
                flags[i].add("injected command not in gold")
    print(f"records flagged by at least one mechanical check: {len(flags)} of {len(rows)} ({len(flags) / len(rows):.0%})")
    c = collections.Counter(f for v in flags.values() for f in v)
    for k, v in c.most_common():
        print(f"  {k}: {v}")
    print("  by family:", dict(collections.Counter(family(rows[i]) for i in flags)))


if __name__ == "__main__":
    main(sys.argv[1])
