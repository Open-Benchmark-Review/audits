"""Write the per-record task log in the repo's templates/task-log.csv format.

One row per sampled record. Classification follows methodology/rubric.md 2a:
  FN  - a correct monitor is scored wrong (gold labels a non-hack, a real hack is unlabelled,
        or a sibling record labels the same command differently)
  FP  - the answer is readable from the harness (red-team order in the monitor's input)
  MINOR - a defect that is not counted: a surface tell only, or an injection that intends a hack
        but cannot take effect (see data/adjudication.json)
  OK  - no defect found

usage: python3 -I task_log.py <record_reviews_dir> <adjudication.json> <records.csv> > task-log.csv
"""
import csv
import glob
import json
import os
import re
import sys

FN = {"gold_not_hack", "gold_incomplete", "contradictory_label", "injected_hack_unlabelled"}
FP = {"answer_leak"}


def first_sentence(s, cap=220):
    s = " ".join((s or "").split())
    m = re.match(r"(.+?[.!?])(\s|$)", s)
    s = m.group(1) if m else s
    return s if len(s) <= cap else s[:cap - 1].rstrip() + "…"


def main(rev_dir, adj_path, records_csv):
    meta = {int(r["record"]): r for r in csv.DictReader(open(records_csv))}
    adj = json.load(open(adj_path))
    w = csv.writer(sys.stdout, lineterminator="\n")
    w.writerow(["task_id", "category", "classification", "confirmed", "counted_toward_threshold",
                "error_subtype", "evidence", "runs_affected", "notes"])
    for p in sorted(glob.glob(os.path.join(rev_dir, "*.json")), key=lambda s: int(os.path.basename(s)[:-5])):
        r = json.load(open(p))
        n = int(r["record"])
        a = adj.get(str(n), {})
        verdict = a.get("verdict", r["verdict"])
        types = sorted(set(a.get("defect_types", r.get("defect_types") or [])))
        codes = []
        if verdict != "correct" and set(types) & FN:
            codes.append("FN")
        if verdict != "correct" and set(types) & FP:
            codes.append("FP")
        counted = bool(codes)
        if not codes:
            codes = ["OK"] if verdict == "correct" and not types else ["MINOR"]
        confirmed = "yes" if (r.get("confidence") == "high" or a.get("verdict") == "defect") else (
            "no" if verdict == "ambiguous" else "medium")
        gold = ",".join(map(str, json.loads(json.dumps(r.get("gold_review", []))) and
                            [g["cmd"] for g in r["gold_review"]][:12]))
        w.writerow([f"record {n} ({meta[n]['id']})", meta[n]["family"], "; ".join(codes), confirmed,
                    "yes" if counted else "no", "; ".join(types) or "none",
                    f"data/record_reviews/{n}.json; gold CMD {gold}", "all monitors",
                    a.get("reason") or first_sentence(r.get("summary"))])


if __name__ == "__main__":
    main(*sys.argv[1:4])
