"""Tally the 50-record review into the Epoch Scoring estimate.

Reads data/record_reviews/<n>.json (reviewer calls) and data/adjudication.json (the lead
auditor's final call where it differs, with a reason), and prints the per-record table and
the defect rate by family, with the rate re-weighted to the full 169-record population.

usage: python3 -I summarize.py <record_reviews_dir> <adjudication.json> <records.csv>
"""
import collections
import csv
import glob
import json
import os
import sys

COUNTED = {"gold_not_hack", "gold_incomplete", "injected_hack_unlabelled",
           "contradictory_label", "answer_leak"}


def main(rev_dir, adj_path, records_csv):
    meta = {int(r["record"]): r for r in csv.DictReader(open(records_csv))}
    adj = json.load(open(adj_path)) if os.path.exists(adj_path) else {}
    pop = collections.Counter(m["family"] for m in meta.values())
    rows = []
    for p in sorted(glob.glob(os.path.join(rev_dir, "*.json")), key=lambda s: int(os.path.basename(s)[:-5])):
        r = json.load(open(p))
        n = int(r["record"])
        a = adj.get(str(n), {})
        types = set(a.get("defect_types", r.get("defect_types") or []))
        verdict = a.get("verdict", r["verdict"])
        counted = bool(types & COUNTED) and verdict != "correct"
        rows.append((n, meta[n]["family"], verdict, sorted(types), counted, a.get("reason", "")))
    print("| record | family | verdict | defect types | counts toward threshold | adjudication note |")
    print("|---|---|---|---|---|---|")
    for n, fam, v, t, c, note in rows:
        print(f"| {n} | {fam} | {v} | {', '.join(t) or '-'} | {'yes' if c else 'no'} | {note} |")
    by = collections.defaultdict(lambda: [0, 0, 0])
    tcount = collections.Counter()
    for n, fam, v, t, c, _ in rows:
        by[fam][0] += 1
        by[fam][1] += c
        by[fam][2] += "surface_tell" in t
        tcount.update(t)
    print()
    print("| family | sampled | with a counted defect | with a surface tell | population |")
    print("|---|---|---|---|---|")
    est = 0.0
    for fam in sorted(by):
        s, d, st = by[fam]
        print(f"| {fam} | {s} | {d} | {st} | {pop[fam]} |")
        est += pop[fam] * d / s
    tot = sum(v[0] for v in by.values())
    cnt = sum(v[1] for v in by.values())
    print(f"| all | {tot} | {cnt} ({cnt / tot:.0%}) | {sum(v[2] for v in by.values())} | {sum(pop.values())} |")
    print()
    print(f"Population-weighted share of records with a counted defect: {est / sum(pop.values()):.0%}")
    print("Defect type counts (records):", dict(tcount.most_common()))


if __name__ == "__main__":
    main(*sys.argv[1:4])
