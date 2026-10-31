"""Sensitivity of the FrontierML ranking (the six audited models) to noise, task choice, review and audit corrections.

usage: python3 -I sensitivity.py <all_trials.csv> [trial_reviews_dir adjudication.json] > data/sensitivity.md

The published score for a model at a wallet is the mean over the 21 tasks of its one trial's score (0-100); this
reproduces the site exactly. Analyses:
  1. Published scores and ranks.
  2. Leave one task out.
  3. Bootstrap over tasks: how often each model holds each rank.
  4. Run-to-run noise. Each (model, task, wallet) is one run. Where a model spent less than $10 at both the $50 and
     $200 wallets, the larger budget went unused, so the two runs are close to replicates; their score gap measures
     noise. Also: how often a larger wallet scored lower.
  5. Reviewer outcomes by model, over all 19 models.
  6. If audit reviews are given: zero the audit's confirmed false positives (and, separately, every reward hack),
     and zero DeepSeek's unreviewed trials that the audit finds would have failed review.
"""
import csv
import glob
import json
import math
import os
import random
import sys
from collections import Counter, defaultdict

MODELS = ['claude-opus-5-5', 'gpt-6-astra', 'claude-fable-5-1', 'gemini-4-argon', 'deepseek-v4-1-flash', 'muse-wonder']
SHORT = {'claude-opus-5-5': 'Opus', 'gpt-6-astra': 'Astra', 'claude-fable-5-1': 'Fable', 'gemini-4-argon': 'Argon',
         'deepseek-v4-1-flash': 'DeepSeek', 'muse-wonder': 'Muse'}
WALLETS = [10, 50, 200]


def table(rows, header):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
    return '\n'.join(out + ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows])


def load(path):
    rows = list(csv.DictReader(open(path)))
    for r in rows:
        r['score'] = 100 * float(r['score'] or 0)
        r['budget'] = int(r['budget'])
        r['compute_usd'] = float(r['compute_usd'] or 0)
        r['trial'] = r['id'][len(r['task']) + 1:]
    return rows


def means(score, tasks, models=MODELS):
    """score[(model, task)] -> mean over tasks."""
    return {m: sum(score[(m, t)] for t in tasks) / len(tasks) for m in models}


def order(mean):
    return sorted(mean, key=lambda m: -mean[m])


def rank_cells(mean, base=None):
    o = order(mean)
    cells = []
    for m in MODELS:
        c = f'{o.index(m) + 1} ({mean[m]:.1f}'
        if base is not None and abs(mean[m] - base[m]) >= 0.05:
            c += f', {mean[m] - base[m]:+.1f}'
        cells.append(c + ')')
    return cells


def fisher_one_sided(a, b, c, d):
    """P(X >= a) for the 2x2 table [[a, b], [c, d]] under the hypergeometric null."""
    n1, n2, k = a + b, c + d, a + c
    tot = math.comb(n1 + n2, k)
    return sum(math.comb(n1, x) * math.comb(n2, k - x) for x in range(a, min(n1, k) + 1)) / tot


def main(path, rdir=None, adj_path=None):
    rows = load(path)
    tasks = sorted({r['task'] for r in rows})
    by = {(r['model'], r['task'], r['budget']): r for r in rows}

    def scores(w, override=None):
        s = {(m, t): by[(m, t, w)]['score'] for m in MODELS for t in tasks}
        for (m, t, ww), v in (override or {}).items():
            if ww == w:
                s[(m, t)] = v
        return s

    print('# FrontierML ranking sensitivity (six audited models)\n')
    print('Cells are rank among the six (score, change from published). Scores are means over 21 tasks, 0-100.\n')
    base = {w: means(scores(w), tasks) for w in WALLETS}

    print('## 1. Published\n')
    print(table([[f'${w}'] + rank_cells(base[w]) for w in WALLETS], ['Wallet'] + [SHORT[m] for m in MODELS]))
    pooled = {m: sum(base[w][m] for w in WALLETS) / 3 for m in MODELS}
    print('\nPooled over the three wallets (63 runs per model): ' +
          ' > '.join(f'{SHORT[m]} {pooled[m]:.1f}' for m in order(pooled)))

    print('\n## 2. Leave one task out ($200)\n')
    changed = []
    for t in tasks:
        mm = means(scores(200), [x for x in tasks if x != t])
        if order(mm) != order(base[200]):
            changed.append([t] + rank_cells(mm, base[200]))
    print(f'{len(tasks) - len(changed)} of {len(tasks)} variants leave the $200 order unchanged.\n')
    if changed:
        print(table(changed, ['Task dropped'] + [SHORT[m] for m in MODELS]))

    print('\n## 3. Bootstrap over tasks (10,000 replicates)\n')
    rng = random.Random(0)
    for w in WALLETS + ['pooled']:
        cnt = defaultdict(Counter)
        for _ in range(10000):
            ts = [rng.choice(tasks) for _ in tasks]
            if w == 'pooled':
                mm = {m: sum(by[(m, t, ww)]['score'] for t in ts for ww in WALLETS) / (3 * len(ts)) for m in MODELS}
            else:
                mm = means(scores(w), ts)
            for i, m in enumerate(order(mm)):
                cnt[m][i + 1] += 1
        label = f'${w}' if w != 'pooled' else 'pooled'
        print(f'**{label}**: share of replicates at each rank\n')
        print(table([[SHORT[m]] + [f'{cnt[m][k] / 100:.0f}%' for k in range(1, 7)] for m in MODELS],
                    ['Model', '1st', '2nd', '3rd', '4th', '5th', '6th']))
        print()

    print('## 4. Run-to-run noise\n')
    pairs = []
    for m in MODELS:
        for t in tasks:
            a, b = by[(m, t, 50)], by[(m, t, 200)]
            if a['compute_usd'] < 10 and b['compute_usd'] < 10:
                pairs.append((m, t, a['score'], b['score']))
    gaps = sorted(abs(x[2] - x[3]) for x in pairs)
    if gaps:
        print(f'{len(pairs)} (model, task) pairs spent under $10 at both the $50 and $200 wallets, so the extra budget '
              f'went unused. Their two runs differ by a median of {gaps[len(gaps) // 2]:.1f} points '
              f'(mean {sum(gaps) / len(gaps):.1f}, max {gaps[-1]:.1f}); {sum(g >= 20 for g in gaps)} differ by 20+ points.\n')
        print(table([[SHORT[m], t, f'{x:.1f}', f'{y:.1f}'] for m, t, x, y in sorted(pairs, key=lambda p: -abs(p[2] - p[3]))[:10]],
                    ['Model', 'Task', '$50 score', '$200 score']))
    print()
    inv = defaultdict(int)
    for m in MODELS:
        for t in tasks:
            s = [by[(m, t, w)]['score'] for w in WALLETS]
            inv[m] += (s[1] < s[0] - 5) + (s[2] < s[1] - 5)
    print('Wallet steps ($10 to $50, $50 to $200) where the larger wallet scored 5+ points lower, of 42 per model: ' +
          ', '.join(f'{SHORT[m]} {inv[m]}' for m in MODELS) + '.')
    gap = sorted(((base[200][a] - base[200][b]), SHORT[a], SHORT[b]) for a, b in zip(order(base[200]), order(base[200])[1:]))
    print('\nGaps between adjacent models at $200: ' + ', '.join(f'{x} > {y} by {g:.1f}' for g, x, y in sorted(gap, key=lambda g: -g[0])) + '.')

    print('\n## 5. Reviewer outcomes, all 19 models\n')
    rv = defaultdict(Counter)
    for r in rows:
        rv[r['model']][r['review'] or 'none'] += 1
    allm = sorted(rv, key=lambda m: (rv[m]['fail'] / 63, m))
    print(table([[m, rv[m]['pass'], rv[m]['fail'], rv[m]['skipped'], rv[m]['incomplete'] + rv[m]['none']] for m in allm],
                ['Model', 'pass', 'fail', 'skipped', 'none / incomplete']))
    cl = [m for m in rv if m.startswith('claude-')]
    a = sum(rv[m]['fail'] for m in cl)
    b = sum(rv[m]['pass'] for m in cl)
    c = sum(rv[m]['fail'] for m in rv if m not in cl)
    d = sum(rv[m]['pass'] for m in rv if m not in cl)
    print(f'\nClaude models: {a} fails of {a + b} reviewed ({a / (a + b):.1%}); other models: {c} of {c + d} ({c / (c + d):.1%}). '
          f'One-sided Fisher exact p (non-Claude fail rate higher) = {fisher_one_sided(c, d, a, b):.4f}. '
          'A lower fail rate can also mean cleaner runs; section 6 and the per-task reviews test which.')

    print('\n## 5b. Does money help, task by task?\n')
    print('FrontierML claims agents turn capital into performance. Per task: mean score of all 19 models at $10 and $200, '
          'and for the six strongest by published $200 score, the mean change, how many improved, and their mean $200 '
          'wallet spend.\n')
    allm = sorted({r['model'] for r in rows})
    full = {(r['model'], r['task'], r['budget']): r for r in rows}
    top6 = sorted(allm, key=lambda m: -sum(full[(m, t, 200)]['score'] for t in tasks))[:6]
    out = []
    for t in tasks:
        a10 = sum(full[(m, t, 10)]['score'] for m in allm) / len(allm)
        a200 = sum(full[(m, t, 200)]['score'] for m in allm) / len(allm)
        d6 = [full[(m, t, 200)]['score'] - full[(m, t, 10)]['score'] for m in top6]
        spend = sum(full[(m, t, 200)]['compute_usd'] for m in top6) / 6
        out.append((sum(d6) / 6, t, a10, a200, sum(x > 0 for x in d6), spend))
    print(table([[t, f'{a10:.1f}', f'{a200:.1f}', f'{a200 - a10:+.1f}', f'{d:+.1f}', f'{w}/6', f'${s:.0f}']
                 for d, t, a10, a200, w, s in sorted(out, reverse=True)],
                ['Task', 'All 19 at $10', 'All 19 at $200', 'Change', 'Top-6 change', 'Top 6 improved', 'Top-6 $200 spend']))
    flat = [t for d, t, *_ in out if d <= 2]
    print(f"\nTop six: {', '.join(SHORT.get(m, m) for m in top6)}. {len(flat)} of {len(tasks)} tasks show a top-6 gain of "
          f"2 points or less from $10 to $200: {', '.join(sorted(flat))}.")

    if not rdir:
        return
    adj = json.load(open(adj_path))
    rev, raw = {}, {}
    for f in sorted(glob.glob(os.path.join(rdir, '*.json'))):
        d = json.load(open(f))
        for t in d['trials']:
            t = dict(t, task=d['task'])
            raw[t['trial']] = dict(t)
            t.update({k: v for k, v in adj.get('trial_overrides', {}).get(t['trial'], {}).items() if k != 'note'})
            rev[t['trial']] = t
    key = {r['trial']: (r['model'], r['task'], r['budget']) for r in rows}
    fp = {key[x]: 0.0 for x in adj.get('confirmed_false_positives', [])}
    hacks = {key[x]: 0.0 for x, t in rev.items() if t['classification'] == 'reward_hack' and x in key}
    fps = {key[x]: 0.0 for x, t in raw.items() if t['grader_agreement'] == 'false_positive' and x in key}
    probable = [x for x, o in adj.get('trial_overrides', {}).items() if 'false positive' in o.get('note', '').lower()
                or x == 'v837u7']
    strict = {**fp, **{key[x]: 0.0 for x in probable if x in key}}
    print('\n## 6. Audit corrections\n')
    sc = [
        ('Published', {}),
        (f'Zero the {len(fp)} confirmed false positives', fp),
        (f"Zero every trial a task reviewer called a false positive, before adjudication ({len(fps)})", fps),
        (f'Strict reading: confirmed plus probable false positives and the contested llm-diffusion winner ({len(strict)})',
         strict),
        (f'Zero every reward hack ({len(hacks)})', hacks),
    ]
    out = []
    for label, o in sc:
        for w in WALLETS:
            out.append([label, f'${w}'] + rank_cells(means(scores(w, o), tasks), base[w]))
    print(table(out, ['Scenario', 'Wallet'] + [SHORT[m] for m in MODELS]))
    fn = [x for x, t in rev.items() if t['grader_agreement'] == 'false_negative']
    if fn:
        print(f"\n{len(fn)} trials were judged false negatives (zeroed but legitimate): {', '.join(sorted(fn))}. "
              'Their pre-review metric is not published, so they cannot be restored here.')


if __name__ == '__main__':
    main(*sys.argv[1:])
