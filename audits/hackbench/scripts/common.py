"""Shared helpers for the HackBench audit scripts.

The dataset is gated (CC BY-NC 4.0, no rehosting), so nothing here writes
transcript text to the repository; scripts print derived statistics only.
"""
import json
import re

CMD_RE = re.compile(r"^\[CMD (\d+)\] ", re.M)


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def split_commands(transcript):
    """Return {index: block_text} for every [CMD n] block in a monitor transcript.

    A block runs from its [CMD n] label to the next [CMD m] label or the next
    top-level [reasoning]/[assistant]/[observation]/[user] marker.
    """
    marks = list(CMD_RE.finditer(transcript))
    stops = [m.start() for m in re.finditer(r"^\[(?:reasoning|assistant|observation|user)\]", transcript, re.M)]
    blocks = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(transcript)
        later = [s for s in stops if m.end() <= s < end]
        if later:
            end = later[0]
        blocks[int(m.group(1))] = transcript[m.end():end]
    return blocks


def family(row):
    """Coarse construction family, read from the record id."""
    i = row["id"]
    if i.startswith("covert__"):
        return "covert-prompted"
    if i.startswith("hbv2__hardneg"):
        return "hbv2-hardneg"
    if i.startswith("hbv2__injected") and "__legit__" in i:
        return "hbv2-injected-legit"
    if i.startswith("hbv2__injected"):
        return "hbv2-injected"
    if row["origin"] == "natural":
        return "natural-red_team" if ("red_team" in i or "-hack-" in i) else "natural-other"
    return "task-specific-generated"
