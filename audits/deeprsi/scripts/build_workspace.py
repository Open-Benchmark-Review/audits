"""Flatten the raw DeepRSI download into a per-task review workspace.

usage: python3 -I build_workspace.py <raw_dir> <workspace_dir>

<workspace_dir>/<task_slug>/task.md                     public overview + the exact task prompt the agent saw
<workspace_dir>/<task_slug>/<model>__<trial>/summary.json  config, reward breakdown, exception, usage
<workspace_dir>/<task_slug>/<model>__<trial>/patch.diff    final submitted patch
<workspace_dir>/<task_slug>/<model>__<trial>/trajectory.txt  every step: user prompts, agent text, reasoning,
                                                            tool calls and (truncated) tool output
<workspace_dir>/trials.csv                              one row per trial
"""
import csv
import glob
import json
import os
import re
import sys

OBS_LIMIT = 4000  # characters of tool output kept per step


def slug(title):
    return re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')


def steps(traj_dir):
    index = json.load(open(os.path.join(traj_dir, 'index.json')))
    out = []
    for i in range(len(index['block_starts'])):
        out.extend(json.load(open(os.path.join(traj_dir, f'block_{i}.json'))))
    return index, out


def flatten(step_list):
    lines = []
    for s in step_list:
        head = f"=== [{s['step_id']}] {s.get('timestamp', '')[:19]} {s['source'].upper()}"
        lines.append(head)
        if s.get('message') and s['message'] != '(tool use)':
            lines.append(s['message'])
        if s.get('reasoning_content'):
            lines.append('<reasoning> ' + s['reasoning_content'].strip())
        for tc in s.get('tool_calls') or []:
            args = tc.get('arguments') or {}
            if tc['function_name'] == 'bash':
                lines.append('$ ' + str(args.get('command', '')))
            elif tc['function_name'] in ('write', 'edit'):
                body = json.dumps(args)
                lines.append(f"<{tc['function_name']}> " + (body if len(body) < OBS_LIMIT else body[:OBS_LIMIT] + ' ...[truncated]'))
            else:
                lines.append(f"<{tc['function_name']}> " + json.dumps(args))
        for r in (s.get('observation') or {}).get('results') or []:
            c = r.get('content') or ''
            if not isinstance(c, str):
                c = json.dumps(c)
            if len(c) > OBS_LIMIT:
                c = c[:OBS_LIMIT // 2] + f'\n...[{len(c) - OBS_LIMIT} chars truncated]...\n' + c[-OBS_LIMIT // 2:]
            lines.append('> ' + c.replace('\n', '\n> '))
    return '\n'.join(lines) + '\n'


def main(raw, ws):
    climb = json.load(open(os.path.join(raw, 'climb.json')))
    tasks = {t['name']: t for t in climb['tasks']}
    rows = []
    written_task = set()
    for f in sorted(glob.glob(os.path.join(raw, 'trials', '*.json'))):
        rec = json.load(open(f))
        task = tasks[rec['task']]
        tdir = os.path.join(ws, slug(task['title']))
        os.makedirs(tdir, exist_ok=True)
        index, st = steps(os.path.join(raw, 'traj', rec['trial']))
        user_msgs = [s['message'] for s in st if s['source'] == 'user']
        if task['name'] not in written_task:
            with open(os.path.join(tdir, 'task.md'), 'w') as fh:
                fh.write(f"# {task['title']}\n\nid: `{task['name']}`\n\ntype: {task['type']}; GPUs: {task['gpu_count']}x "
                         f"{','.join(task['gpus']) or 'none'}; env: {task['environment']}\n\n## Public overview\n\n"
                         f"{task['overview']}\n\n## Task prompt given to the agent (step 1 of trial {rec['trial']})\n\n"
                         f"{user_msgs[0] if user_msgs else '(missing)'}\n")
            written_task.add(task['name'])
        short = rec['trial'].split('__')[-1]
        trdir = os.path.join(tdir, f"{rec['model']}__{short}")
        os.makedirs(trdir, exist_ok=True)
        fm = rec.get('final_metrics') or {}
        summary = {k: rec.get(k) for k in ('trial', 'model', 'model_provider', 'reasoning_effort', 'agent', 'agent_version',
                                            'started_at', 'finished_at', 'agent_seconds', 'reward', 'rewards', 'exception')}
        summary['final_metrics'] = fm
        summary['n_steps'] = len(st)
        summary['user_messages'] = user_msgs
        json.dump(summary, open(os.path.join(trdir, 'summary.json'), 'w'), indent=1)
        with open(os.path.join(trdir, 'patch.diff'), 'w') as fh:
            for pf in (rec.get('patch') or {}).get('files') or []:
                fh.write((pf.get('diff') or f"# {pf['path']} ({pf['status']}, no diff)\n") + '\n')
        with open(os.path.join(trdir, 'trajectory.txt'), 'w') as fh:
            fh.write(flatten(st))
        r = rec.get('rewards') or {}
        rows.append(dict(task=slug(task['title']), task_type=task['type'], model=rec['model'], trial=short,
                         provider=rec['model_provider'], effort=rec.get('reasoning_effort'),
                         started=rec['started_at'], agent_seconds=rec.get('agent_seconds'), reward=rec.get('reward'),
                         valid=r.get('valid'), disqualified=r.get('disqualified'), objective=r.get('objective'),
                         baseline_objective=r.get('baseline_objective'), has_breakdown=bool(r),
                         exception=(rec.get('exception') or {}).get('type'), steps=len(st),
                         user_turns=len(user_msgs), cost_usd=fm.get('total_cost_usd'),
                         prompt_tokens=fm.get('total_prompt_tokens'), completion_tokens=fm.get('total_completion_tokens'),
                         peak_context=(fm.get('extra') or {}).get('peak_context_tokens')))
    with open(os.path.join(ws, 'trials.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f'{len(rows)} trials, {len(written_task)} tasks -> {ws}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
