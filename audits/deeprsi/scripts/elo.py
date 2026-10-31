"""Re-implementation of the DeepRSI leaderboard Elo, from the method text embedded in the site bundles.

Method (quoted from results-*.js / elo-intervals-*.js):
  - "Each task is one game between each two models: the share of their runs' comparisons that one won,
    where the higher reward wins and an exact tie counts as half a win."
  - Bradley-Terry fit "with 0.0569 virtual draws added to every pair so that every strength is finite".
  - "The original field of 5 models is fitted on its own and its Elo is frozen; each later model is rated
    against that field alone." (Gemini 4 Argon was run ten days after the other five.)
  - "The scale gives the field's final ratings a population standard deviation of 350."
  - "The centre is set so that the starter rates exactly 0: one more player whose every run scores what
    the unchanged starter does, rated against the field's fitted strengths."
  - Disqualified attempts score the starter's value (reward 0).

usage: python3 -I elo.py <trials.csv> [overrides.json]
  overrides.json (optional): {"<trial id>": <reward>} applied before rating, e.g. to zero out attempts an
  audit judges to be reward hacks.
"""
import csv
import itertools
import json
import math
import random
import sys
from collections import defaultdict

FIELD = ['gpt-6-astra', 'claude-fable-5.1', 'grok-4.7', 'kimi-k3', 'gemini-3.8-flash']
LATER = ['gemini-4-argon']
PRIOR = 0.0569
SCALE = 598.1905515407495  # frozen by the site; recomputed below as a check
PUBLISHED = {'gpt-6-astra': 1232.08, 'claude-fable-5.1': 1548.19, 'grok-4.7': 685.24, 'kimi-k3': 820.13,
             'gemini-3.8-flash': 642.62, 'gemini-4-argon': 964.86}
STARTER = 'starter'
# "excluded_ungraded_trials" from the leaderboard bundle (results-*.js): trials with no graded waypoint
EXCLUDED = {'SBRceHp', 'ZSBYrDS', '6evhdYQ'}


def load(path, overrides=None, excluded=EXCLUDED):
    runs = defaultdict(lambda: defaultdict(list))  # task -> model -> [reward]
    for r in csv.DictReader(open(path)):
        if r['trial'] in excluded:
            continue
        rew = float(r['reward'] or 0)
        if overrides and r['trial'] in overrides:
            rew = overrides[r['trial']]
        runs[r['task']][r['model']].append(rew)
    for task in runs:
        runs[task][STARTER] = [0.0]
    return runs


def game(a, b, tie_tol=0.0):
    """Share of pairwise run comparisons a wins over b (ties = 1/2). tie_tol: relative tolerance for a tie."""
    w = 0.0
    for x in a:
        for y in b:
            if abs(x - y) <= tie_tol * max(abs(x), abs(y)) or x == y:
                w += 0.5
            elif x > y:
                w += 1
    return w / (len(a) * len(b))


def tally(runs, players, tie_tol=0.0):
    wins = defaultdict(float)  # (i, j) -> wins of i over j, summed over tasks
    games = defaultdict(float)
    for task, by_model in runs.items():
        for i, j in itertools.combinations(players, 2):
            if by_model.get(i) and by_model.get(j):
                g = game(by_model[i], by_model[j], tie_tol)
                wins[i, j] += g
                wins[j, i] += 1 - g
                games[i, j] += 1
                games[j, i] += 1
    # PRIOR virtual draws per pair: PRIOR extra games, each player credited half of them
    for i, j in itertools.combinations(players, 2):
        wins[i, j] += PRIOR / 2
        wins[j, i] += PRIOR / 2
        games[i, j] += PRIOR
        games[j, i] += PRIOR
    return wins, games


def fit(players, wins, games, fixed=None, iters=5000):
    """Bradley-Terry MLE by minorisation-maximisation. fixed: {player: strength} held constant."""
    fixed = fixed or {}
    p = {i: fixed.get(i, 1.0) for i in players}
    for _ in range(iters):
        new = {}
        for i in players:
            if i in fixed:
                new[i] = fixed[i]
                continue
            w = sum(wins[i, j] for j in players if j != i)
            d = sum(games[i, j] / (p[i] + p[j]) for j in players if j != i)
            new[i] = w / d if d else p[i]
        if not fixed:
            g = math.exp(sum(math.log(v) for v in new.values()) / len(new))
            new = {k: v / g for k, v in new.items()}
        if max(abs(math.log(new[i] / p[i])) for i in players) < 1e-12:
            p = new
            break
        p = new
    return p


def rate_against(runs, player, field_strengths, tie_tol=0.0):
    players = list(field_strengths) + [player]
    wins, games = tally(runs, players, tie_tol)
    fixed = dict(field_strengths)
    # only the games between `player` and the field matter once the field is fixed
    return fit(players, wins, games, fixed=fixed)[player]


def ratings(runs, tie_tol=0.0, scale=None):
    wins, games = tally(runs, FIELD, tie_tol)
    p = fit(FIELD, wins, games)
    logs = {m: math.log10(v) for m, v in p.items()}
    if scale is None:
        mean = sum(logs.values()) / len(logs)
        sd = math.sqrt(sum((v - mean) ** 2 for v in logs.values()) / len(logs))
        scale = 350 / sd if sd else SCALE
    out = {m: scale * logs[m] for m in FIELD}
    for m in LATER + [STARTER]:
        out[m] = scale * math.log10(rate_against(runs, m, p, tie_tol))
    off = out[STARTER]
    return {m: v - off for m, v in out.items()}, scale


def ranking(r):
    return [m for m, _ in sorted(((m, v) for m, v in r.items() if m != STARTER), key=lambda kv: -kv[1])]


def main():
    runs = load(sys.argv[1], json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None)
    r, scale = ratings(runs, scale=SCALE)
    _, own_scale = ratings(runs)
    print(f'scale used {SCALE:.2f}; scale recomputed from this data {own_scale:.2f}')
    for m in ranking(r):
        print(f'  {m:18s} {r[m]:8.1f}   published {PUBLISHED.get(m, float("nan")):8.1f}')


if __name__ == '__main__':
    main()
