"""Aggregate the per-trial reviews (with lead-auditor adjudication) into the tables used in README.md.

usage: python3 -I summarize.py <trial_reviews_dir> <adjudication.json> > data/summary.md
"""
import glob
import json
import os
import sys
from collections import Counter, defaultdict

CLASSES = ['research', 'engineering', 'grey_area', 'reward_hack', 'no_gain']
MODELS = ['claude-fable-5.1', 'gpt-6-astra', 'gemini-4-argon', 'kimi-k3', 'grok-4.7', 'gemini-3.8-flash']


def table(rows, header):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
    return '\n'.join(out + ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows])


def main(rdir, adj_path):
    adj = json.load(open(adj_path))
    trials, tasks = [], {}
    for f in sorted(glob.glob(os.path.join(rdir, '*.json'))):
        d = json.load(open(f))
        tl = dict(d['task_level'])
        tl.update({k: v for k, v in adj['task_overrides'].get(d['task'], {}).items() if k != 'note'})
        tasks[d['task']] = tl
        for t in d['trials']:
            t = dict(t, task=d['task'])
            t.update({k: v for k, v in adj['trial_overrides'].get(t['trial'], {}).items() if k != 'note'})
            if t['trial'] in adj['confirmed_false_positives']:
                t['grader_agreement'] = 'false_positive'
            trials.append(t)

    n = len(trials)
    c = Counter(t['classification'] for t in trials)
    print('## What produced the scores (all 180 attempts, adjudicated)\n')
    print(table([[k, c[k], f'{c[k] / n:.0%}'] for k in CLASSES], ['Classification', 'Attempts', 'Share']))
    nov = Counter(t['novelty'] for t in trials if t['classification'] in ('research', 'engineering'))
    print(f'\nNovelty among legitimate attempts: ' + ', '.join(f'{k} {v}' for k, v in nov.most_common()))

    print('\n## By model\n')
    rows = []
    for m in MODELS:
        mc = Counter(t['classification'] for t in trials if t['model'] == m)
        fp = sum(1 for t in trials if t['model'] == m and t['grader_agreement'] == 'false_positive')
        rows.append([m] + [mc[k] for k in CLASSES] + [fp])
    print(table(rows, ['Model'] + CLASSES + ['confirmed false positives']))

    print('\n## By task\n')
    rows = []
    for task, tl in tasks.items():
        tc = Counter(t['classification'] for t in trials if t['task'] == task)
        rows.append([task] + [tc[k] for k in CLASSES] + [tl['epoch_scoring_item']])
    print(table(rows, ['Task'] + CLASSES + ['Epoch scoring item']))

    print('\n## Attempts the official grade got wrong or cannot support\n')
    rows = []
    for t in sorted(trials, key=lambda t: (t['grader_agreement'], t['task'])):
        if t['grader_agreement'] == 'agree':
            continue
        note = adj['confirmed_false_positives'].get(t['trial']) or adj['probable_false_positives'].get(t['trial']) \
            or adj['trial_overrides'].get(t['trial'], {}).get('note') or t['evidence'][0]
        rows.append([t['grader_agreement'], t['task'], t['model'], t['trial'], f"{t['official_reward']:.2f}",
                     t['official_status'], note.replace('|', '/')])
    print(table(rows, ['Call', 'Task', 'Model', 'Trial', 'Official reward', 'Official status', 'Why']))

    print('\n## Attempts classified as research\n')
    rows = [[t['task'], t['model'], t['trial'], t['novelty'], t['approach'].replace('|', '/')]
            for t in trials if t['classification'] == 'research']
    print(table(rows, ['Task', 'Model', 'Trial', 'Novelty', 'Approach']))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
