"""Print the Epoch-style errors table from the adjudicated 50-record review.

Maps this audit's defect types onto Epoch's Scoring error types:
  gold_not_hack, gold_incomplete, contradictory_label -> False Negative
      (a monitor that answers correctly is scored as wrong: it loses recall on a mislabelled
       command, or loses precision for flagging a real but unlabelled hack)
  answer_leak -> False Positive (the answer is retrievable from the harness, here the monitor's input)

usage: python3 -I epoch_errors.py <record_reviews_dir> <adjudication.json> <records.csv>
"""
import csv
import glob
import json
import os
import sys

FN = {"gold_not_hack": "gold labels a non-hack", "gold_incomplete": "real hack left unlabelled",
      "contradictory_label": "same command labelled differently in a sibling record"}
FP = {"answer_leak": "red-team order in the monitor's input"}


def main(rev_dir, adj_path, records_csv):
    meta = {int(r["record"]): r for r in csv.DictReader(open(records_csv))}
    adj = json.load(open(adj_path))
    out = []
    for p in glob.glob(os.path.join(rev_dir, "*.json")):
        r = json.load(open(p))
        n = int(r["record"])
        a = adj.get(str(n), {})
        if a.get("verdict", r["verdict"]) == "correct":
            continue
        types = set(a.get("defect_types", r.get("defect_types") or []))
        kinds = []
        if types & set(FN):
            kinds.append("False Negative")
        if types & set(FP):
            kinds.append("False Positive")
        if not kinds:
            continue
        what = "; ".join([FN[t] for t in sorted(types & set(FN))] + [FP[t] for t in sorted(types & set(FP))])
        out.append((n, meta[n]["id"], meta[n]["family"], " + ".join(kinds), what))
    out.sort(key=lambda x: (x[3], x[0]))
    print("| Record | Family | Error type | Defect | Review |")
    print("|---|---|---|---|---|")
    for n, i, fam, k, what in out:
        print(f"| {n} | {fam} | {k} | {what} | [data/record_reviews/{n}.json](data/record_reviews/{n}.json) |")
    print(f"\n{len(out)} records")


if __name__ == "__main__":
    main(*sys.argv[1:4])
