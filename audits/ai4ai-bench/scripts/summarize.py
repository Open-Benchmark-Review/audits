"""Aggregate the AI4AI-Bench task reviews (with adjudication) into the tables used in report.md.

usage: python3 -I summarize.py <task_reviews_dir> <adjudication.json> > ../data/summary.md
"""
import glob
import json
import os
import sys
from collections import Counter

CLASSES = ['research', 'engineering', 'grey_area', 'reward_hack', 'no_gain']
MODELS = ['claude-opus-5', 'gpt-5.6-sol', 'kimi-k3', 'claude-sonnet-5', 'gpt-5.6-terra', 'gpt-5.6-luna']


def table(rows, header):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
    return '\n'.join(out + ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows])


def main(rdir, adj_path):
    adj = json.load(open(adj_path))
    tasks, cells = {}, []
    for f in sorted(glob.glob(os.path.join(rdir, '*.json'))):
        d = json.load(open(f))
        tl = dict(d['task_level'])
        tl.update({k: v for k, v in adj['task_overrides'].get(d['task'], {}).items() if k != 'note'})
        tasks[d['task']] = tl
        for c in d['cells']:
            cells.append(dict(c, task=d['task']))
    n = len(cells)
    cc = Counter(c['classification'] for c in cells)
    print(f'## What produced the scores (all {n} cells)\n')
    print(table([[k, cc[k], f'{cc[k] / n:.0%}'] for k in CLASSES], ['Classification', 'Cells', 'Share']))
    nov = Counter(c['novelty'] for c in cells if c['classification'] in ('research', 'engineering'))
    print('\nNovelty among legitimate cells: ' + ', '.join(f'{k} {v}' for k, v in nov.most_common()))
    print('\n## By model\n')
    rows = []
    for m in MODELS:
        mc = Counter(c['classification'] for c in cells if c['model'] == m)
        ga = Counter(c['grader_agreement'] for c in cells if c['model'] == m)
        rows.append([m, sum(mc.values())] + [mc[k] for k in CLASSES] + [ga['false_positive'], ga['false_negative']])
    print(table(rows, ['Model', 'Cells'] + CLASSES + ['false positives', 'false negatives']))
    print('\n## By task\n')
    rows = []
    for t, tl in tasks.items():
        tc = Counter(c['classification'] for c in cells if c['task'] == t)
        ga = Counter(c['grader_agreement'] for c in cells if c['task'] == t)
        rows.append([t] + [tc[k] for k in CLASSES] + [ga['false_positive'], ga['false_negative'], tl['rubric_code'],
                                                       'yes' if tl['counted_toward_threshold'] else 'no'])
    print(table(rows, ['Task'] + CLASSES + ['FP cells', 'FN cells', 'Rubric code', 'Counted']))
    counted = [t for t, tl in tasks.items() if tl['counted_toward_threshold']]
    print(f'\nCounted toward the threshold: {len(counted)} of {len(tasks)} tasks ({len(counted) / len(tasks):.0%}): '
          + ', '.join(counted))
    print('\n## Cells the official result got wrong or cannot support\n')
    rows = []
    for c in sorted(cells, key=lambda c: (c['grader_agreement'], c['task'], c['case'])):
        if c['grader_agreement'] == 'agree':
            continue
        ev = (c['evidence'][0] if c['evidence'] else '').replace('|', '/')
        rows.append([c['grader_agreement'], c['task'], c['model'], c['effort'], c['official_best'], ev[:260]])
    print(table(rows, ['Call', 'Task', 'Model', 'Effort', 'Official best', 'Evidence']))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
