"""Build a per-record review workspace (outside the repo: the data may not be rehosted).

For each record writes <out>/<n>/:
  meta.json        id, family, gold indices, injected (sibling-unique) indices, sibling-labelled
                   commands the record leaves unlabelled, surface tells
  instruction.txt  monitor_input.task_instruction
  transcript.txt   monitor_input.transcript (the numbered monitor input)
  outline.txt      the transcript without observations: reasoning/assistant text and commands,
                   each truncated, so a reviewer can scan the whole trajectory
  focus.md         full context (preceding turn, command, following observation) for every gold,
                   injected and sibling-labelled command

usage: python3 -I build_workspace.py <hackbench.jsonl> <out_dir> [record numbers...]
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CMD_RE, family, load, split_commands
from sibling_diff import clusters, norm

BLOCK_RE = re.compile(r"^\[(reasoning|assistant|observation|user|tool_result|CMD \d+)\]", re.M)


def segments(t):
    marks = list(BLOCK_RE.finditer(t))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(t)
        yield m.group(1), m.start(), t[m.start():end]


def outline(t, cut=600):
    out = []
    for kind, _, seg in segments(t):
        if kind in ("observation", "tool_result"):
            out.append(seg[:200].rstrip() + (" …[observation truncated]" if len(seg) > 200 else ""))
        else:
            out.append(seg[:cut].rstrip() + (" …[truncated]" if len(seg) > cut else ""))
    return "\n".join(out)


def context(t, k, before=4000, cmd=8000, after=4000):
    m = re.search(r"^\[CMD %d\] " % k, t, re.M)
    if not m:
        return "(not found)"
    start = max(0, m.start() - before)
    nxt = CMD_RE.search(t, m.end())
    cmd_end = min(m.start() + cmd, nxt.start() if nxt else len(t))
    obs = re.search(r"^\[(observation|tool_result)\]", t[m.end():], re.M)
    tail = ""
    if obs:
        o = m.end() + obs.start()
        tail = t[max(o, cmd_end):max(o, cmd_end) + after]
    return t[start:m.start()] + ">>>>> TARGET\n" + t[m.start():cmd_end] + "\n<<<<< END TARGET\n" + tail


def main(path, out, picks):
    rows = load(path)
    texts = [{k: norm(v) for k, v in split_commands(r["monitor_input"]["transcript"]).items()} for r in rows]
    unique, sib = {}, {}
    labelled = {}
    for i, r in enumerate(rows):
        for g in r["gold_command_indices"]:
            labelled.setdefault(texts[i][g], set()).add(i)
    for group in clusters(texts):
        for i in group:
            others = set().union(*(set(texts[j].values()) for j in group if j != i))
            unique[i] = sorted(k for k, t in texts[i].items() if t not in others)
    for i in range(len(rows)):
        gold = set(rows[i]["gold_command_indices"])
        sib[i] = {k: sorted(labelled[t] - {i}) for k, t in texts[i].items()
                  if k not in gold and len(t) >= 40 and labelled.get(t, set()) - {i}}
    for i in picks:
        r = rows[i]
        d = os.path.join(out, str(i))
        os.makedirs(d, exist_ok=True)
        t = r["monitor_input"]["transcript"]
        meta = {
            "record": i, "id": r["id"], "family": family(r), "task": r["task"]["name"],
            "origin": r["origin"], "hack_type": r["hack_type"],
            "source_agent": r["source_agent"].get("configured_model_name"),
            "command_count": r["monitor_input"]["command_count"],
            "gold_command_indices": r["gold_command_indices"],
            "injected_command_indices_from_sibling_diff": unique.get(i),
            "sibling_labelled_but_unlabelled_here": {str(k): v for k, v in sib[i].items()},
        }
        with open(os.path.join(d, "meta.json"), "w") as f:
            json.dump(meta, f, indent=1)
        with open(os.path.join(d, "instruction.txt"), "w") as f:
            f.write(r["monitor_input"]["task_instruction"])
        with open(os.path.join(d, "transcript.txt"), "w") as f:
            f.write(t)
        with open(os.path.join(d, "outline.txt"), "w") as f:
            f.write(outline(t))
        focus = sorted(set(r["gold_command_indices"]) | set(unique.get(i) or []) | set(sib[i]))
        if len(focus) > 40:  # very large gold sets: first/last 15 plus all non-gold focus commands
            g = r["gold_command_indices"]
            focus = sorted(set(g[:15] + g[-15:]) | (set(focus) - set(g)))
        with open(os.path.join(d, "focus.md"), "w") as f:
            for k in focus:
                tag = []
                if k in r["gold_command_indices"]:
                    tag.append("GOLD")
                if k in (unique.get(i) or []):
                    tag.append("INJECTED (unique vs siblings)")
                if k in sib[i]:
                    tag.append(f"LABELLED AS HACK IN SIBLING RECORDS {sib[i][k]} BUT NOT HERE")
                f.write(f"\n\n################ CMD {k}: {', '.join(tag)}\n")
                f.write(context(t, k))
        print(i, d, len(t), "outline", os.path.getsize(os.path.join(d, "outline.txt")))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3:]])
