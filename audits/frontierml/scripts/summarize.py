"""Aggregate the per-trial reviews (with lead-auditor adjudication) into the tables used in README.md.

usage: python3 -I summarize.py <trial_reviews_dir> <adjudication.json> > data/summary.md
"""
import glob
import json
import os
import sys
from collections import Counter

CLASSES = ['research', 'engineering', 'grey_area', 'reward_hack', 'no_gain']
MODELS = ['claude-opus-5-5', 'gpt-6-astra', 'claude-fable-5-1', 'gemini-4-argon', 'deepseek-v4-1-flash', 'muse-wonder']


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
    print(f'## What produced the scores (all {n} audited trials, adjudicated)\n')
    print(table([[k, c[k], f'{c[k] / n:.0%}'] for k in CLASSES], ['Classification', 'Trials', 'Share']))
    nov = Counter(t['novelty'] for t in trials if t['classification'] in ('research', 'engineering'))
    print('\nNovelty among legitimate trials: ' + ', '.join(f'{k} {v}' for k, v in nov.most_common()))

    print('\n## By model\n')
    rows = []
    for m in MODELS:
        mt = [t for t in trials if t['model'] == m]
        mc = Counter(t['classification'] for t in mt)
        ga = Counter(t['grader_agreement'] for t in mt)
        rows.append([m] + [mc[k] for k in CLASSES] +
                    [ga['false_positive'], ga['false_negative'], sum(t['infra_issue'] == 'confirmed' for t in mt)])
    print(table(rows, ['Model'] + CLASSES + ['false positives', 'false negatives', 'confirmed infra issues']))

    print('\n## Reviewer (Opus 5.5) assessment by model\n')
    ra = ['sound', 'missed_violation', 'wrong_violation', 'skipped', 'not_applicable']
    print(table([[m] + [Counter(t['reviewer_assessment'] for t in trials if t['model'] == m)[k] for k in ra] for m in MODELS],
                ['Model'] + ra))

    print('\n## By task\n')
    rows = []
    for task in sorted(tasks):
        tc = Counter(t['classification'] for t in trials if t['task'] == task)
        rows.append([task] + [tc[k] for k in CLASSES] + [tasks[task]['epoch_scoring_item']])
    print(table(rows, ['Task'] + CLASSES + ['Epoch scoring item']))

    print('\n## Trials the official grade got wrong or cannot support\n')
    rows = []
    for t in sorted(trials, key=lambda t: (t['grader_agreement'], t['task'], t['model'], t['wallet'])):
        if t['grader_agreement'] == 'agree' and t['infra_issue'] != 'confirmed':
            continue
        why = adj['trial_overrides'].get(t['trial'], {}).get('note') or (t['evidence'][0] if t['evidence'] else '')
        rows.append([t['grader_agreement'], t['task'], t['model'], f"${t['wallet']}", t['trial'],
                     f"{t['official_score']:.1f}", t['official_review'], t['infra_issue'], why.replace('|', '/')])
    print(table(rows, ['Call', 'Task', 'Model', 'Wallet', 'Trial', 'Official score', 'Review', 'Infra', 'Why']))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
