"""Do injected commands touch files that exist in the trajectory?

For every record whose injected command is identifiable by sibling diff, extract the
file names the command reads or edits (.py/.json/.yaml/.toml/.gin/.sh/.txt/.csv/.pt) and
check whether each name appears anywhere else in the transcript (file listings, earlier
edits, later runs). An injection whose every target file is mentioned nowhere else edits
a file the environment never shows; it cannot have changed the graded result, and the
"patched" observation that follows it is inconsistent with the world state.

usage: python3 -I injection_targets.py <hackbench.jsonl>
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import family, load, split_commands
from sibling_diff import clusters, norm

FILE_RE = re.compile(r"[\w\-]+(?:/[\w\-.]+)*\.(?:py|json|yaml|yml|toml|gin|sh|txt|csv|pt|tsv|jsonl)\b")
SKIP = {"/dev/null"}


def main(path):
    rows = load(path)
    raw = [split_commands(r["monitor_input"]["transcript"]) for r in rows]
    texts = [{k: norm(v) for k, v in b.items()} for b in raw]
    tally = collections.Counter()
    print("| record | family | injected CMD | in gold | target files | targets seen elsewhere |")
    print("|---|---|---|---|---|---|")
    for group in clusters(texts):
        for i in group:
            others = set().union(*(set(texts[j].values()) for j in group if j != i))
            uniq = [k for k, t in texts[i].items() if t not in others]
            if len(uniq) != 1:
                continue
            k = uniq[0]
            cmd = raw[i][k]
            t = rows[i]["monitor_input"]["transcript"]
            rest = t.replace(cmd, "")
            files = sorted({f for f in FILE_RE.findall(cmd) if f not in SKIP})
            seen = [f for f in files if os.path.basename(f) in rest]
            fam = family(rows[i])
            ingold = k in rows[i]["gold_command_indices"]
            tally[(fam, "injected")] += 1
            tally[(fam, "no_target_seen")] += bool(files) and not seen
            print(f"| {i} | {fam} | {k} | {'yes' if ingold else 'no'} | {len(files)} | {len(seen)} |")
    print()
    for fam in sorted({f for f, _ in tally}):
        print(f"{fam}: {tally[(fam, 'no_target_seen')]} of {tally[(fam, 'injected')]} injected commands "
              f"touch only files that appear nowhere else in the transcript")


if __name__ == "__main__":
    main(sys.argv[1])
