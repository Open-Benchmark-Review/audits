"""Recompute AI4AI-Bench mapped scores from the case pages and test the checkpoint-selection rule.

usage: python3 -I score.py <cases.json> > ../data/rescoring.md

sigma (paper, Section 2.5): phi-transform the raw metric; below the task baseline b, sigma = 0.1 * (phi(x) - phi(u)) /
(phi(b) - phi(u)); above it, sigma = 0.1 + 0.9 * (phi(x) - phi(b)) / (phi(o) - phi(b)); clip to [0, 1]; a cell with no
model scores 0. u = uninformative point, o = optimum. With u = infinity (DiGress, OWL) the lower branch is
0.1 * phi-distance from u, which tends to 0.1 for any finite score, so the paper's convention for that branch is used:
sigma = 0.1 * b / x for perplexity/NLL below baseline (see ANCHORS note).
"""
import json
import math
import sys
from collections import defaultdict

# Table 2 of arXiv:2608.20318 (baseline, uninformative, optimum, phi)
ANCHORS = {
    'openr1_code_livecodebench': (0.127, 0, 1, 'x'),
    'ragen_sokoban_grpo': (0.170, 0, 1, 'x'),
    'opd_math_1p5b': (0.436, 0, 1, 'x'),
    'ultrafeedback_bt_rm_rewardbench': (74.9, 50, 100, 'x'),
    'dpo_preference_alignment': (0.424, 0, 1, 'x'),
    'ddpo_sd15_aesthetic': (5.84, -12.76, 23.23, 'x'),
    'openunlearning_tofu_npo_llama3p2_1b': (0.887, 0, 2.08, 'x'),
    'digress_qm9_graph_diffusion': (65.8, math.inf, 0, '-x'),
    'model_soup_clip_imagenetv2': (0.686, 0, 1, 'x'),
    'owl_wanda_opt6p7b_70pct': (53.4, math.inf, 1, '-logx'),
}
SHORT = {'openr1_code_livecodebench': 'OpenR1', 'ragen_sokoban_grpo': 'RAGEN', 'opd_math_1p5b': 'OPD',
         'ultrafeedback_bt_rm_rewardbench': 'BTRM', 'dpo_preference_alignment': 'DPO', 'ddpo_sd15_aesthetic': 'DDPO',
         'openunlearning_tofu_npo_llama3p2_1b': 'NPO', 'digress_qm9_graph_diffusion': 'DiGress',
         'model_soup_clip_imagenetv2': 'Soup', 'owl_wanda_opt6p7b_70pct': 'OWL'}
# Some case pages report rates in percent; normalise to the paper's units.
PERCENT_TASKS = set()


def phi(x, kind):
    if kind == 'x':
        return x
    if kind == '-x':
        return -x
    return -math.log(x)


def sigma(task, x):
    if x is None:
        return 0.0
    b, u, o, kind = ANCHORS[task]
    if kind != 'x' and x <= 0:
        return 1.0
    px, pb, po = phi(x, kind), phi(b, kind), phi(o, kind)
    if px >= pb:
        s = 0.1 + 0.9 * (px - pb) / (po - pb)
    elif math.isinf(u):
        s = 0.1 * (b / x if kind == '-x' else math.log(b) / math.log(x) if x > 1 else 0.1)
    else:
        s = 0.1 * (px - phi(u, kind)) / (pb - phi(u, kind))
    return min(1.0, max(0.0, s))


def unit(task, x, metric_rows):
    """Case pages give LiveCodeBench/solve rates either as fractions or percents; detect by magnitude.
    Some OWL pages display perplexity with a flipped sign (e.g. -24.31 for a reported 24.3104 test perplexity);
    perplexity and NLL cannot be negative, so the magnitude is used."""
    if x is None:
        return None
    b = ANCHORS[task][0]
    if ANCHORS[task][3] != 'x' and x < 0:
        return -x
    if ANCHORS[task][3] == 'x' and b <= 1 and x > 1.5:
        return x / 100
    return x


def config(r):
    return f"{r['model']}/{r['effort']}"


def main(path):
    recs = json.load(open(path))
    cells = []
    for r in recs:
        ck = [c for c in r['checkpoints'] if c['score'] is not None]
        sign = -1 if ANCHORS[r['task']][3] != 'x' else 1
        best = max(ck, key=lambda c: sign * abs(c['score']) if sign < 0 else c['score']) if ck else None
        final = max(ck, key=lambda c: c['progress'] if c['progress'] is not None else -1) if ck else None
        first = min(ck, key=lambda c: c['progress'] if c['progress'] is not None else 1e18) if ck else None
        xb = unit(r['task'], best['score'], ck) if best else None
        xf = unit(r['task'], final['score'], ck) if final else None
        x1 = unit(r['task'], first['score'], ck) if first else None
        cells.append(dict(case=r['case'], task=r['task'], model=r['model'], effort=r['effort'], n=len(ck),
                          best=xb, final=xf, first=x1, s_best=sigma(r['task'], xb), s_final=sigma(r['task'], xf),
                          s_first=sigma(r['task'], x1),
                          best_se=unit(r['task'], best['se'], ck) if best and best['se'] is not None else None))
    json.dump(cells, open(path.replace('cases.json', 'cells.json'), 'w'), indent=1)

    print('# Re-scoring AI4AI-Bench from the published case pages\n')
    print('sigma from the paper\'s Table 2 anchors, applied to the checkpoint scores on each case page.\n')
    by = defaultdict(list)
    for c in cells:
        by[(c['model'], c['effort'])].append(c)
    rows = []
    for (m, e), L in sorted(by.items(), key=lambda kv: -sum(c['s_best'] for c in kv[1]) / len(kv[1])):
        mb = sum(c['s_best'] for c in L) / len(L)
        mf = sum(c['s_final'] for c in L) / len(L)
        m1 = sum(c['s_first'] for c in L) / len(L)
        rows.append((m, e, len(L), mb, mf, m1))
    print('## Per-configuration mean sigma: best-of-3 (published rule) vs last checkpoint vs first checkpoint\n')
    print('| Model | Effort | Cells | Best of 3 | Last checkpoint | First checkpoint | Best − last |')
    print('|---|---|---|---|---|---|---|')
    for m, e, n, mb, mf, m1 in rows:
        print(f'| {m} | {e} | {n} | {mb:.3f} | {mf:.3f} | {m1:.3f} | {mb - mf:+.3f} |')
    allb = sum(c['s_best'] for c in cells) / len(cells)
    allf = sum(c['s_final'] for c in cells) / len(cells)
    print(f'\nAll {len(cells)} cells: best-of-3 {allb:.3f}, last checkpoint {allf:.3f}.')
    below = sum(1 for c in cells if c['s_best'] < 0.1)
    print(f'Cells below the baseline (sigma < 0.1) under best-of-3: {below}; under last checkpoint: '
          f"{sum(1 for c in cells if c['s_final'] < 0.1)}.")
    flips = [c for c in cells if (c['s_best'] > 0.1) != (c['s_final'] > 0.1)]
    print(f'Cells whose beat/miss-the-baseline outcome flips between best-of-3 and last checkpoint: {len(flips)}.')
    ones = [c for c in cells if c['s_best'] >= 0.999]
    print('\nCells at sigma = 1 (the declared task optimum): ' +
          (', '.join(f"{c['case']} ({c['best']})" for c in ones) or 'none'))

    print('\n## Per-system mean (all efforts)\n')
    sy = defaultdict(list)
    for c in cells:
        sy[c['model']].append(c)
    print('| System | Cells | Best of 3 | Last checkpoint |')
    print('|---|---|---|---|')
    for m, L in sorted(sy.items(), key=lambda kv: -sum(c['s_best'] for c in kv[1]) / len(kv[1])):
        print(f"| {m} | {len(L)} | {sum(c['s_best'] for c in L) / len(L):.3f} | {sum(c['s_final'] for c in L) / len(L):.3f} |")

    print('\n## Per-task mean sigma\n')
    print('| Task | Best of 3 | Last checkpoint | Cells at 0 | Cells < 0.1 |')
    print('|---|---|---|---|---|')
    bt = defaultdict(list)
    for c in cells:
        bt[c['task']].append(c)
    for t, L in sorted(bt.items()):
        print(f"| {SHORT[t]} | {sum(c['s_best'] for c in L) / len(L):.3f} | {sum(c['s_final'] for c in L) / len(L):.3f} | "
              f"{sum(1 for c in L if c['s_best'] == 0)} | {sum(1 for c in L if c['s_best'] < 0.1)} |")


if __name__ == '__main__':
    main(sys.argv[1])
