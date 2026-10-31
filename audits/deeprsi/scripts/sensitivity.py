"""Sensitivity of the DeepRSI ranking to scoring choices, using the verified Elo re-implementation (elo.py).

usage: python3 -I sensitivity.py <trials.csv> [trial_reviews_dir adjudication.json] > data/sensitivity.md

Analyses:
  1. Published method (reproduces the leaderboard exactly).
  2. Count the three "ungraded" trials the leaderboard drops, although each has a private-verifier grade.
  3. Treat reward differences within a relative tolerance as ties (verifier timing noise).
  4. Leave one task out.
  5. Bootstrap over tasks and attempts: how often each model holds each rank.
  6. Head-to-head task wins between the top two models.
  7. If audit reviews are given: zero out attempts the audit classifies as reward hacks (and, separately,
     reward hacks plus grey-area attempts), or restore attempts the audit judges wrongly disqualified.
"""
import csv
import glob
import json
import os
import random
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import elo  # noqa: E402

MODELS = elo.FIELD + elo.LATER


def fmt(r):
    return ' > '.join(f'{m} ({r[m]:.0f})' for m in elo.ranking(r))


def short(m):
    return {'gpt-6-astra': 'Astra', 'claude-fable-5.1': 'Fable', 'grok-4.7': 'Grok', 'kimi-k3': 'Kimi',
            'gemini-3.8-flash': 'Flash', 'gemini-4-argon': 'Argon'}[m]


def table(rows, header):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
    out += ['| ' + ' | '.join(str(c) for c in row) + ' |' for row in rows]
    return '\n'.join(out)


def rank_row(label, r, base):
    order = elo.ranking(r)
    cells = [label]
    for m in MODELS:
        d = r[m] - base[m]
        cells.append(f'{order.index(m) + 1} ({r[m]:.0f}, {d:+.0f})' if abs(d) >= 0.5 else f'{order.index(m) + 1} ({r[m]:.0f})')
    return cells


def load_reviews(d):
    out = {}
    for f in glob.glob(os.path.join(d, '*.json')):
        for t in json.load(open(f))['trials']:
            out[t['trial']] = t
    return out


def main():
    path = sys.argv[1]
    reviews = load_reviews(sys.argv[2]) if len(sys.argv) > 2 else {}
    base_runs = elo.load(path)
    base, _ = elo.ratings(base_runs, scale=elo.SCALE)
    header = ['Scenario'] + [short(m) for m in MODELS]
    rows = [rank_row('Published method (reproduced)', base, base)]

    allruns = elo.load(path, excluded=set())
    rows.append(rank_row('Count the 3 dropped "ungraded" trials', elo.ratings(allruns, scale=elo.SCALE)[0], base))
    for tol in (0.01, 0.02, 0.05):
        rows.append(rank_row(f'Rewards within {tol:.0%} count as ties', elo.ratings(base_runs, tie_tol=tol, scale=elo.SCALE)[0], base))

    if reviews:
        adj = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
        for t, o in adj.get('trial_overrides', {}).items():
            reviews[t] = {**reviews[t], **{k: v for k, v in o.items() if k != 'note'}}
        conf = {t: 0.0 for t in adj.get('confirmed_false_positives', {})}
        prob = {**conf, **{t: 0.0 for t in adj.get('probable_false_positives', {})}}
        # cross-entropy attempts disqualified under the rule missing from the prompt, restored to their
        # graded speedup (reward = objective / baseline - 1); z3Viy4a has no graded objective and stays at 0
        lifted = {}
        for r in csv.DictReader(open(path)):
            if r['task'].startswith('large-vocabulary') and r['disqualified'] and r['objective']:
                lifted[r['trial']] = max(0.0, float(r['objective']) / float(r['baseline_objective']) - 1)
        strict = {t: 0.0 for t, v in reviews.items() if v['classification'] in ('reward_hack', 'grey_area')}
        scen = [
            (f'Zero confirmed false positives ({len(conf)} trials)', conf),
            (f'Zero confirmed + probable false positives ({len(prob)})', prob),
            (f'Lift hidden-rule cross-entropy disqualifications ({len(lifted)})', lifted),
            ('Both of the previous two', {**prob, **lifted}),
            (f'Strict: zero every reward-hack or grey-area attempt ({len(strict)})', strict),
        ]
        for label, ov in scen:
            rows.append(rank_row(label, elo.ratings(elo.load(path, ov), scale=elo.SCALE)[0], base))

    print('## Ranking under alternative scoring choices\n')
    print('Each cell: rank (Elo, change vs published). Elo scale and centre follow the published method.\n')
    print(table(rows, header))

    # leave one task out
    print('\n## Leave one task out\n')
    lot = []
    for task in sorted(base_runs):
        runs = {t: v for t, v in base_runs.items() if t != task}
        r, _ = elo.ratings(runs, scale=elo.SCALE)
        changed = elo.ranking(r) != elo.ranking(base)
        lot.append([task, ' > '.join(short(m) for m in elo.ranking(r)), 'yes' if changed else ''])
    print(table(lot, ['Task removed', 'Ranking', 'Order changes']))

    # bootstrap
    random.seed(20261027)
    n = 1000
    counts = {m: Counter() for m in MODELS}
    tasks = sorted(base_runs)
    for _ in range(n):
        runs = {}
        for k, t in enumerate(random.choices(tasks, k=len(tasks))):
            runs[f'{t}#{k}'] = {m: (random.choices(v, k=len(v)) if m != elo.STARTER else v) for m, v in base_runs[t].items()}
        r, _ = elo.ratings(runs, scale=elo.SCALE)
        for i, m in enumerate(elo.ranking(r)):
            counts[m][i + 1] += 1
    print(f'\n## Bootstrap rank distribution ({n} replicates; tasks and attempts resampled)\n')
    print(table([[short(m)] + [f'{counts[m][k] / n:.0%}' for k in range(1, 7)] for m in elo.ranking(base)],
                ['Model', '#1', '#2', '#3', '#4', '#5', '#6']))

    # head to head per task
    print('\n## Per-task results\n')
    print('Mean reward per model and task (the starter scores 0). Bold marks the task winner by Elo game score.\n')
    rows = []
    wins = Counter()
    for task in sorted(base_runs):
        by = base_runs[task]
        score = {m: sum(elo.game(by[m], by[o]) for o in MODELS if o != m and by.get(o)) for m in MODELS if by.get(m)}
        best = max(score, key=score.get)
        wins[best] += 1
        rows.append([task] + [(f'**{sum(by[m]) / len(by[m]):.2f}**' if m == best else f'{sum(by[m]) / len(by[m]):.2f}') if by.get(m) else '–' for m in MODELS])
    print(table(rows, ['Task'] + [short(m) for m in MODELS]))
    print('\nTask wins: ' + ', '.join(f'{short(m)} {c}' for m, c in wins.most_common()))
    f, a = 'claude-fable-5.1', 'gpt-6-astra'
    h2h = [elo.game(base_runs[t][f], base_runs[t][a]) for t in tasks]
    print(f'\nFable vs Astra, task by task (share of attempt comparisons Fable won): ' +
          ', '.join(f'{x:.2f}' for x in h2h) + f'; Fable ahead on {sum(x > 0.5 for x in h2h)}, '
          f'level on {sum(x == 0.5 for x in h2h)}, behind on {sum(x < 0.5 for x in h2h)} of {len(h2h)} tasks.')


if __name__ == '__main__':
    main()
