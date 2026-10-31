"""Flatten the raw FrontierML download into a per-task review workspace.

usage: python3 -I build_workspace.py <raw_dir> <workspace_dir>

<workspace_dir>/<task>/task.md                       the exact task prompt the agents saw, and its variants
<workspace_dir>/<task>/<model>__<trial>/summary.json  trial record, harness, run id, every user-turn message
<workspace_dir>/<task>/<model>__<trial>/grade.txt     the published grade page: score scaling, raw metric,
                                                      verifier details, each reviewer check, self-check log
<workspace_dir>/<task>/<model>__<trial>/trajectory.txt  every step: user prompts, agent text, reasoning,
                                                      tool calls and (truncated) tool output
<workspace_dir>/trials.csv                            one row per audited trial
"""
import csv
import gzip
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_site  # noqa: E402

OBS_LIMIT = 4000  # characters of tool output kept per step


def flatten(steps):
    lines = []
    for s in steps:
        lines.append(f"=== [{s['i']}] {s.get('ts', '')[:19]} {s['src'].upper()}")
        if s.get('msg'):
            lines.append(s['msg'])
        if s.get('think'):
            lines.append('<reasoning> ' + s['think'].strip())
        for t in s.get('tools') or []:
            a = t.get('args') or ''
            lines.append(f"<{t.get('name')}> " + (a if len(a) < OBS_LIMIT else a[:OBS_LIMIT] + ' ...[truncated]'))
        for o in s.get('obs') or []:
            c = o.get('text') or ''
            if len(c) > OBS_LIMIT:
                c = c[:OBS_LIMIT // 2] + f'\n...[{len(c) - OBS_LIMIT} chars truncated]...\n' + c[-OBS_LIMIT // 2:]
            lines.append('> ' + c.replace('\n', '\n> '))
    return '\n'.join(lines) + '\n'


def task_prompt(steps):
    """The user turn carrying the task (harnesses wrap it differently; Codex sends an environment turn first)."""
    for s in steps:
        if s['src'] == 'user' and 'CONTRACT.md' in s['msg']:
            m = s['msg']
            m = re.sub(r'^\s*<USER_REQUEST>\s*', '', m)
            return m.split('</USER_REQUEST>')[0].strip()
    return None


def main(raw, ws):
    recs = {r['id']: r for r in json.load(open(os.path.join(raw, 'trials.json')))}
    trajids = json.load(open(os.path.join(raw, 'trajids.json')))
    rows, prompts = [], defaultdict(lambda: defaultdict(list))
    for tid, trajid in sorted(trajids.items()):
        r = recs[tid]
        d = json.load(gzip.open(os.path.join(raw, 'traj', f'{trajid}.json.gz')))
        st = d['steps']
        grade = parse_site.text(os.path.join(raw, 'pages', f'{tid}.html'))
        head = re.search(r'Trial · \S+ (.*?) Wallet \$10', grade)
        hm = re.search(r'(\S+) Harness (.+)$', head.group(1)) if head else None
        short = tid[len(r['task']) + 1:]
        tdir = os.path.join(ws, r['task'])
        trdir = os.path.join(tdir, f"{r['model']}__{short}")
        os.makedirs(trdir, exist_ok=True)
        prompt = task_prompt(st)
        prompts[r['task']][prompt].append(f"{r['model']} ${r['budget']} {short}")
        user_msgs = [s['msg'] for s in st if s['src'] == 'user']
        run = re.search(r'-(\d{8})(?:-r(\d+))?$', trajid)
        summary = dict(r, trial=short, trajectory_id=trajid, agent=d['agent'], effort=hm.group(1) if hm else None,
                       harness=hm.group(2) if hm else None, run_date=run.group(1), rerun=int(run.group(2) or 1),
                       started=st[0].get('ts'), finished=st[-1].get('ts'), n_steps=len(st), user_messages=user_msgs)
        json.dump(summary, open(os.path.join(trdir, 'summary.json'), 'w'), indent=1)
        open(os.path.join(trdir, 'grade.txt'), 'w').write(grade + '\n')
        open(os.path.join(trdir, 'trajectory.txt'), 'w').write(flatten(st))
        rows.append(dict(task=r['task'], model=r['model'], trial=short, wallet=r['budget'], score=r['score'],
                         review=r['review'], selfchecks=r['selfchecks_used'], agent_hours=r['agent_hours'],
                         wallet_spend=r['compute_usd'], api_usd=r['api_usd'], steps=r['steps'],
                         harness=summary['harness'], effort=summary['effort'], run_date=summary['run_date'],
                         rerun=summary['rerun'], started=summary['started'], trajectory_id=trajid))
    for task, variants in prompts.items():
        ranked = sorted(variants.items(), key=lambda kv: -len(kv[1]))
        with open(os.path.join(ws, task, 'task.md'), 'w') as fh:
            fh.write(f'# {task}\n\n## Task prompt given to the agents ({len(ranked[0][1])} of 18 trials)\n\n{ranked[0][0]}\n')
            for p, who in ranked[1:]:
                fh.write(f"\n## Variant prompt ({', '.join(who)})\n\n{p}\n")
    rows.sort(key=lambda x: (x['task'], x['model'], x['wallet']))
    with open(os.path.join(ws, 'trials.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f'{len(rows)} trials, {len(prompts)} tasks -> {ws}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
