"""Write a per-record index (metadata only, no transcript text) as CSV.

Record numbers are 0-based line numbers in the released JSONL and are used throughout this audit.

usage: python3 -I index.py <hackbench.jsonl> > data/records.csv
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import family, load, split_commands
from heuristics import turns
from sibling_diff import clusters, norm


def main(path):
    rows = load(path)
    texts = [{k: norm(v) for k, v in split_commands(r["monitor_input"]["transcript"]).items()} for r in rows]
    cid = {}
    for c, g in enumerate(clusters(texts)):
        for i in g:
            cid[i] = c
    w = csv.writer(sys.stdout)
    w.writerow(["record", "id", "family", "task", "origin", "hack_type", "source_agent", "commands",
                "gold", "base_cluster", "instruction_has_red_team_prompt", "gold_has_fake_host_prompt"])
    for i, r in enumerate(rows):
        tt = turns(r["monitor_input"]["transcript"])
        fake = any(re.search(r"root@host[:\s]", tt[k][1]) for k in r["gold_command_indices"])
        w.writerow([i, r["id"], family(r), r["task"]["name"], r["origin"], r["hack_type"],
                    r["source_agent"].get("configured_model_name"), r["monitor_input"]["command_count"],
                    len(r["gold_command_indices"]), cid.get(i, ""),
                    int("red-team agent" in r["monitor_input"]["task_instruction"]), int(fake)])


if __name__ == "__main__":
    main(sys.argv[1])
