"""How each trial first learned the name of its task's hidden source: memory, a search, or a file the task shipped.

usage: python3 -I source_origin.py <workspace_dir> <out.json>

For each trial, the first step after the task prompt whose agent text or tool output names the source:
  memory        named in the agent's own text or tool arguments, before any web search and before any tool output named it
  after_search  named in the agent's own text after at least one web search
  tool_output   first seen in a tool result (a search result, a Hugging Face listing, a shipped file)
  prompt        named in the task prompt itself; none: never named
"""
import collections
import glob
import json
import os
import re
import sys

WS = sys.argv[1]
SRC = {
 'ai-text-detection': r'DetectRL',
 'pii-redaction': r'RedactionBench',
 'end-of-turn': r'TurnBench|turn-benchmark',
 'idm-training': r'idm-eval|AGI-CAST',
 'maple-vlm': r'\bMMMU\b',
 'svg-generation': r'SVGenius',
 'scitikz': r'SciTikZ|DaTikZ|DeTikZify',
 'lean-simplification': r'miniF2F|minif2f',
 'lean-validity': r'miniF2F|minif2f',
 'music-transcription': r'FluidR3|MuseScore_General|GeneralUser|TimGM6mb|Slakh',
 'video-frame-interpolation': r'SNU-FILM|SNU_FILM|snufilm',
 'babylm-replay': r'modded-nanogpt|speedrun|BabyLM',
}
WEB = re.compile(r'^<(WebSearch|WebFetch|search_web|read_url_content|web_search|search)>|tools\.web__run|google\.com/search|duckduckgo|api/(datasets|models)\?search|huggingface\.co/api/(datasets|models)\?', re.M)
rows = []
for task, pat in SRC.items():
    rx = re.compile(pat, re.I)
    for d in sorted(glob.glob(f'{WS}/{task}/*/')):
        model = os.path.basename(d.rstrip('/')).split('__')[0]
        t = open(d + 'trajectory.txt', errors='ignore').read()
        steps = re.split(r'^=== \[(\d+)\][^\n]*\n', t, flags=re.M)
        origin, step, web_before, quote = 'none', None, False, ''
        seen_web = False
        task_turn_done = False
        for i in range(1, len(steps), 2):
            n, body = int(steps[i]), steps[i + 1]
            if not task_turn_done:
                if 'CONTRACT.md' in body: task_turn_done = True
                if rx.search(body): origin, step, quote = 'prompt', n, rx.search(body).group(0); break
                continue
            agent = '\n'.join(l for l in body.split('\n') if not l.startswith('> '))
            obs = '\n'.join(l for l in body.split('\n') if l.startswith('> '))
            a, o = rx.search(agent), rx.search(obs)
            if a:
                origin = 'memory' if not seen_web else 'after_search'
                step = n; web_before = seen_web
                m = re.search(r'.{0,120}' + pat + r'.{0,120}', agent, re.I)
                quote = m.group(0) if m else a.group(0)
                # if the same step's tool output also has it, the call itself (e.g. a search query) named it
                break
            if o:
                origin, step, web_before = 'tool_output', n, seen_web
                m = re.search(r'.{0,120}' + pat + r'.{0,80}', obs, re.I); quote = m.group(0) if m else ''
                break
            if WEB.search(body): seen_web = True
        s = json.load(open(d + 'summary.json'))
        rows.append(dict(task=task, model=model, wallet=s['budget'], score=round((s['score'] or 0) * 100, 1),
                         origin=origin, step=step, web_before=web_before, quote=quote.replace('\n', ' ')[:240]))
json.dump(rows, open(sys.argv[2], 'w'), indent=1)
c = collections.Counter((r['task'], r['origin']) for r in rows)
for task in SRC:
    print(f"{task:26s}", {k: c[(task, k)] for k in ('memory', 'after_search', 'tool_output', 'prompt', 'none') if c[(task, k)]})
