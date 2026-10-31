"""How robust is AI4AI-Bench's system ranking to aggregation and to the contaminated Sokoban task?

usage: python3 -I ranking.py <cells.json> [task_reviews_dir] > ../data/ranking.md

cells.json comes from score.py (one row per cell with sigma under best-of-3 and last-checkpoint selection).
"""
import json
import os
import random
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score  # noqa: E402

SYSTEMS = ['claude-opus-5', 'gpt-5.6-sol', 'kimi-k3', 'claude-sonnet-5', 'gpt-5.6-terra', 'gpt-5.6-luna']
SHORT = {'claude-opus-5': 'Opus 5', 'gpt-5.6-sol': 'Sol', 'kimi-k3': 'Kimi K3', 'claude-sonnet-5': 'Sonnet 5',
         'gpt-5.6-terra': 'Terra', 'gpt-5.6-luna': 'Luna'}


def mean(xs):
    return sum(xs) / len(xs) if xs else float('nan')


def system_scores(cells, key='s_best', efforts=None, tasks=None, agg='mean'):
    by = defaultdict(lambda: defaultdict(list))  # system -> effort -> [sigma]
    for c in cells:
        if tasks is not None and c['task'] not in tasks:
            continue
        if efforts is not None and c['effort'] not in efforts and c['model'] != 'kimi-k3':
            continue
        by[c['model']][c['effort']].append(c[key])
    out = {}
    for m, eff in by.items():
        cfg = {e: mean(v) for e, v in eff.items()}
        out[m] = max(cfg.values()) if agg == 'best' else mean([x for v in eff.values() for x in v])
    return out


def rank_line(label, s):
    order = sorted(s, key=lambda m: -s[m])
    return '| ' + label + ' | ' + ' > '.join(f'{SHORT[m]} ({s[m]:.3f})' for m in order) + ' |'


def main(path):
    cells = json.load(open(path))
    tasks = sorted({c['task'] for c in cells})
    print('# AI4AI-Bench ranking sensitivity\n')
    print('| Aggregation | System order (mean σ) |')
    print('|---|---|')
    print(rank_line('Published: mean over all effort levels, best-of-3', system_scores(cells)))
    print(rank_line('Last checkpoint instead of best-of-3', system_scores(cells, 's_final')))
    print(rank_line('Max effort only (Kimi K3 ran only at max)', system_scores(cells, efforts={'max'})))
    print(rank_line("Each system's best configuration", system_scores(cells, agg='best')))
    print(rank_line('Exclude effort "none" and "low"', system_scores(cells, efforts={'medium', 'high', 'xhigh', 'max'})))
    no_ragen = [t for t in tasks if t != 'ragen_sokoban_grpo']
    print(rank_line('Drop RAGEN (train/final board contamination)', system_scores(cells, tasks=set(no_ragen))))
    capped = [dict(c, s_best=min(c['s_best'], 0.1 + 0.9 * 0.0) if c['task'] == 'ragen_sokoban_grpo' and c['s_best'] >= 0.999 else c['s_best']) for c in cells]
    print(rank_line('RAGEN σ=1 cells (512/512) set to baseline', system_scores(capped)))

    # all confirmed corrections together (see data/adjudication.json)
    if len(sys.argv) > 2:
        reviews = {}
        for t in tasks:
            f = os.path.join(sys.argv[2], t + '.json')
            if os.path.exists(f):
                for c in json.load(open(f))['cells']:
                    reviews[c['case']] = c
        anchors = dict(score.ANCHORS)
        anchors['openunlearning_tofu_npo_llama3p2_1b'] = (0.887, 0, 1.0, 'x')
        anchors['ultrafeedback_bt_rm_rewardbench'] = (74.568936, 50, 100, 'x')
        anchors['openr1_code_livecodebench'] = (0.12286, 0, 1, 'x')
        saved = score.ANCHORS
        score.ANCHORS = anchors
        corrected = []
        for c in cells:
            if c['task'] == 'ragen_sokoban_grpo':
                continue
            s_new = score.sigma(c['task'], c['best'])
            if c['task'] == 'ddpo_sd15_aesthetic' and reviews.get(c['case'], {}).get('grader_agreement') == 'false_positive':
                s_new = min(s_new, 0.1)
            corrected.append(dict(c, s_best=s_new))
        score.ANCHORS = saved
        print(rank_line('All confirmed corrections (NPO optimum 1.0; task-stated BTRM/OpenR1 baselines; '
                        'DDPO degenerate cells capped at baseline; RAGEN dropped)', system_scores(corrected)))
        print(rank_line('All confirmed corrections, max effort only', system_scores(corrected, efforts={'max'})))

    # effort noise: same model, adjacent effort levels
    print('\n## Run-to-run noise proxy\n')
    print('There is one run per cell. Differences between adjacent effort levels of the same model mix effort effects '
          'with run noise; non-monotone effort curves bound the noise from below.\n')
    order = ['none', 'low', 'medium', 'high', 'xhigh', 'max']
    for m in SYSTEMS:
        if m == 'kimi-k3':
            continue
        cfg = {e: mean([c['s_best'] for c in cells if c['model'] == m and c['effort'] == e]) for e in order}
        seq = [(e, cfg[e]) for e in order if cfg[e] == cfg[e]]
        print(f"- {SHORT[m]}: " + ', '.join(f'{e} {v:.3f}' for e, v in seq))

    # task bootstrap of the configuration ranking and the system ranking
    random.seed(20261029)
    n = 2000
    sys_rank = {m: Counter() for m in SYSTEMS}
    for _ in range(n):
        tb = random.choices(tasks, k=len(tasks))
        s = {}
        for m in SYSTEMS:
            vals = []
            for t in tb:
                vals += [c['s_best'] for c in cells if c['model'] == m and c['task'] == t]
            s[m] = mean(vals)
        for i, m in enumerate(sorted(s, key=lambda k: -s[k])):
            sys_rank[m][i + 1] += 1
    print(f'\n## Task bootstrap of the published system ranking ({n} replicates)\n')
    print('| System | #1 | #2 | #3 | #4 | #5 | #6 |')
    print('|---|---|---|---|---|---|---|')
    for m in sorted(SYSTEMS, key=lambda m: -sys_rank[m][1] * 10 - sys_rank[m][2]):
        print(f'| {SHORT[m]} | ' + ' | '.join(f'{sys_rank[m][k] / n:.0%}' for k in range(1, 7)) + ' |')

    # how much of each system's mean comes from RAGEN
    print('\n## Contribution of RAGEN to each system\'s mean σ\n')
    print('| System | Mean σ | Mean σ without RAGEN | RAGEN cells at σ = 1 |')
    print('|---|---|---|---|')
    for m in SYSTEMS:
        allv = [c['s_best'] for c in cells if c['model'] == m]
        nr = [c['s_best'] for c in cells if c['model'] == m and c['task'] != 'ragen_sokoban_grpo']
        ones = sum(1 for c in cells if c['model'] == m and c['task'] == 'ragen_sokoban_grpo' and c['s_best'] >= 0.999)
        print(f'| {SHORT[m]} | {mean(allv):.3f} | {mean(nr):.3f} | {ones} |')


if __name__ == '__main__':
    main(sys.argv[1])
