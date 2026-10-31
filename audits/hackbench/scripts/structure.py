"""Dataset structure: base-trajectory clusters, gold-set sizes, and label-consistency ceilings.

usage: python3 -I structure.py <hackbench.jsonl>
"""
import collections
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import family, load, split_commands
from heuristics import macro, score
from sibling_diff import clusters, norm


def main(path):
    rows = load(path)
    texts = [{k: norm(v) for k, v in split_commands(r["monitor_input"]["transcript"]).items()} for r in rows]
    groups = clusters(texts)
    cid = {}
    for c, g in enumerate(groups):
        for i in g:
            cid[i] = c
    nxt = len(groups)
    for i in range(len(rows)):
        if i not in cid:
            cid[i] = nxt
            nxt += 1
    sizes = sorted(collections.Counter(cid.values()).values(), reverse=True)
    print(f"records: {len(rows)}; distinct base trajectories: {len(set(cid.values()))}")
    print(f"largest base-trajectory clusters (records): {sizes[:8]}")
    print(f"share of records in the 3 largest clusters: {sum(sizes[:3]) / len(rows):.0%}")
    syn = [i for i, r in enumerate(rows) if r["origin"] == "synthetic"]
    print(f"synthetic records: {len(syn)} from {len({cid[i] for i in syn})} base trajectories")
    print(f"effective N if clusters are the unit (Kish, equal record weights): "
          f"{len(rows) ** 2 / sum(s * s for s in sizes):.1f}")

    g = [len(r["gold_command_indices"]) for r in rows]
    print(f"gold set size: median {statistics.median(g)}, mean {statistics.mean(g):.1f}, max {max(g)}; "
          f"records with >20 gold: {sum(x > 20 for x in g)} holding {sum(x for x in g if x > 20)} of {sum(g)} gold commands")

    # ceilings
    labelled = collections.defaultdict(set)
    for i, r in enumerate(rows):
        for k in r["gold_command_indices"]:
            labelled[texts[i][k]].add(i)
    union_pred, scores_union = [], []
    for i, r in enumerate(rows):
        gold = set(r["gold_command_indices"])
        extra = {k for k, t in texts[i].items() if len(t) >= 40 and labelled.get(t, set()) - {i}}
        scores_union.append(score(gold | extra, gold))
    p, rr, f = macro(scores_union)
    print(f"monitor flagging every command the benchmark labels a hack in this record OR a sibling: "
          f"P {p:.1f} R {rr:.1f} F1 {f:.1f} (a perfect, consistent monitor is capped here)")

    # cluster bootstrap vs record bootstrap of a fixed per-record score (record-level F1 of that monitor)
    per = [s[2] for s in scores_union]
    rng = random.Random(0)
    def boot(unit_ids):
        units = collections.defaultdict(list)
        for i, u in enumerate(unit_ids):
            units[u].append(i)
        keys = list(units)
        vals = []
        for _ in range(4000):
            pick = [rng.choice(keys) for _ in keys]
            idx = [i for k in pick for i in units[k]]
            vals.append(100 * sum(per[i] for i in idx) / len(idx))
        vals.sort()
        return vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals))]
    lo, hi = boot(list(range(len(rows))))
    clo, chi = boot([cid[i] for i in range(len(rows))])
    print(f"95% bootstrap interval for that monitor's F1: resampling records {lo:.1f}-{hi:.1f} "
          f"(width {hi - lo:.1f}); resampling base trajectories {clo:.1f}-{chi:.1f} (width {chi - clo:.1f})")


if __name__ == "__main__":
    main(sys.argv[1])
