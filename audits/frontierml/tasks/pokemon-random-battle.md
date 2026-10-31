# Pokémon Random Battle (pokemon-random-battle)

## The task

The agent builds a Gen 9 Random Battle singles bot and serves batched decisions at `POST /act`.

- **Opponent:** the pinned Foul Play bot, at 100 ms per sampled state.
- **Games:** 3,000 games from 1,500 fixed private matchups, each played from both sides.
- **Deadline:** every response (up to 32 observations) must arrive within 1 s on an H100 box with 8 CPU cores. A late response forfeits every game in that batch.
- **What is allowed:** unchanged or modified Foul Play is a valid submission, and so is validation-guided selection (`tests/task/review.py:62-84`).

## How scoring works

- **Metric:** reward = clamp((mean_battle_points - 0.5)/0.5, 0, 1) (task.yaml:115-118). Draws count 0.5, and a game capped at 200 turns counts as a loss.
- **Noise:** the paired standard error is about 0.0083 raw, or **1.66 reward points**.
- **Reviewer checks:** provenance, served policy, permitted information and credentials.

## Results

| Model | $10 | $50 | $200 |
|---|---|---|---|
| Claude Opus 5.5 | 0 (8i7wzs, 0.497) | **7.4** (5ynzr7) | 2.7 (5yrulw) |
| Claude Fable 5.1 | 0.1 (46sb14) | 1.0 (1ivy96) | 1.5 (zntfdz) |
| GPT-6 Astra | **6.4** (gldk67) | 7.2 (5phq1t, 116 timeout forfeits) | 3.1 (2ithii) |
| Gemini 4 Argon | 3.3 (mqu25j) | 0 (3rg468, 0.496) | **3.6** (59idzz) |
| DeepSeek V4.1 Flash | 0 (4n26hl, 0.485) | 6.1 (4ypkgp) | 0 (59vn26, 0.495) |
| Muse Wonder | 0 (q76m16, 0.492) | 0 (3oxwfl, 0.430, 308 timeout forfeits) | 0 (5tdndb, 0.458) |

All 18 trials passed review. My verdicts:

- **Engineering:** 10 trials.
- **No gain:** 8 trials, all at or below a mirror match.
- **Violations:** none. My verdict agrees with the grader on every trial.

## What the models did

Every bot is built on the same core: vendored Foul Play reconstructs the battle from the public log, opponent sets are sampled from the shipped priors, and poke-engine MCTS runs in an 8-process pool on a 0.75-0.9 s budget. The models differ in what they add on top:

- **Opus 5ynzr7** (best score, 7.4) added an opponent model that predicts Foul Play's choice from Foul Play's point of view, plus a one-turn lookahead re-rank ([163] `bot/oppmodel.py`).
- **Astra** added value-net reranking:
  - gldk67 used the public Laplace value net, unchanged.
  - 5phq1t and 2ithii trained value nets on self-play.
- **Others** made small search changes: more samples, deterministic argmax, weighted set sampling.

## Key findings

1. **No rule violations or grading errors.**
   - No trial accessed the private matchups, the benchmark repo or frontierml.org.
   - Some bots cache reconstructed battle state across requests: DeepSeek 4ypkgp's LRU [612], and the Muse bots. This conflicts with CONTRACT.md's "treat requests as stateless", but no action is cached and the reviewer policy has no stateless check.
2. **Timeout forfeits are self-inflicted, but they matter.**
   - Astra 5phq1t ran at median 0.911 s / p95 0.920 s in its final selfcheck. Its own validation saw "a slowest response of 0.924 seconds" [1287]. It lost 116 games to the 1 s deadline.
   - Had those games been played at its 53.6% rate, it would have scored about 11, beating Opus's 7.4 at $50.
   - The selfcheck warned that late-game logs are longer, so I do not count this as infrastructure.
   - Muse 3oxwfl's 308 forfeits do not matter: it stays below 50% either way.
3. **The task barely separates the models.**
   - Every submission is a Foul Play derivative, so raw scores sit at 0.43-0.54 and 8 of 18 trials are clamped to 0.
   - The winners are within about 1 standard error of the runners-up at $50 and $200, and about 2 at $10.
   - Spending more does not help: Opus $200 spent $111 and scored below its $50 run.

## Epoch scoring item: **pass**

- **No scoring defects:** I found no false positive, false negative or infrastructure zero.
- **Winners:** Astra ($10), Opus ($50) and Gemini ($200). Each would plausibly change on a rerun.
- **Measurement quality:** this noise is a problem with how precisely the task measures, not a scoring defect.

## Task design

- **The spec is consistent but long.** The instruction, CONTRACT and `task.yaml` agree. The 1 s per-batch deadline, the late-batch forfeit, the clamp at 50% and the 200-turn loss rule all appear only in CONTRACT.md:11, not in the instruction. The CONTRACT says "Treat requests as stateless" (CONTRACT.md:7), but the review policy has no stateless check (`tests/task/review.py:61-85`), so state-caching bots pass.
- **The floor sits at parity with the opponent, and it was never calibrated.** "User-selected anchors: 0 = 50% ... not an empirically calibrated self-play result" (`tests/task/task.yaml:119-123`). The opponent searches about 200 ms per decision (`tests/task/pipeline/README.md:34-35`). The candidate must answer up to 32 games in 1 s on 8 cores (`tests/task/pokemon_random_battle.py:24`, CONTRACT.md:30), about the same compute, and it re-parses the whole public log each time. A faithful Foul Play rebuild therefore lands at 0.485-0.497 raw and scores 0. "Unchanged Foul Play" (`instruction.md:1`) cannot even be served unchanged through the batched API.
- **The floor is binding and erases information.** 41 of 57 trials score 0. A broken bot (raw 0.43) and an exact mirror (raw 0.497) get the same 0. The organizer's own baselines sit far below the floor: a type heuristic won 1 of 32 (`README.md:247-249`), and the Astra pilot's 237/640 "would earn zero" (`README.md:149-150`).
- **Noise dominates the usable range.** The paired SE is 0.0083 raw, or 1.66 points (`pokemon_random_battle.py:319`). The observed range is 0-11.9, and most gaps between models are 1-2 SE. The clamp is a hinge at the mode: 0.497 scores 0 and 0.5077 scores 1.5. Foul Play's time-based search adds variance between runs (CONTRACT.md:11).
- **The opponent's strength depends on the hardware.** Its MCTS is time-based on 16 shared verifier CPUs, and the organizer notes that "hardware contention can affect exact MCTS decisions". No full H100 grade was calibrated after the scheduling change (`README.md:117-119, 130-131`). This moves where parity falls (suspected magnitude).
- **The latency gate has a heavy penalty and thin self-check coverage.** A late response forfeits the whole batch, about 30 games or about 2 points (CONTRACT.md:11). The self-check samples up to 124 mostly early-game requests out of about 3,722 (`tests/task/verifier.py:33`), and it gives no win-rate signal. Astra 5phq1t lost 116 games, about 4 points, which is as large as the gaps between winners. The 18,000 s execution budget can never bind: at most 1 s x 3,722 requests is 3,722 s.
- **Budget does not help.** The wallet means are 0.6 / 1.9 / 0.6, and Opus's $111 $200 run scored below its $50 run. Measuring a gain of a few percent needs thousands of games, but the public validator plays 32 (an SE of about 17.7 points). Rented CPU at $0.14 per core-hour makes larger tests affordable even at $10.
- **Outcome rules.** Capped games are candidate losses (`tests/task/pokemon_random_battle_sim.js:181-182`), and an illegal opponent choice is a candidate win (line 216). Each happens at most once per trial. This is fine.
- **Neutrality.** No judge and no vendor element. Foul Play, the priors and the poke-engine wheel ship in `/task/public`, so every harness starts from the same bot.
- **Reference solution.** It is the smoke fixture, which always plays action 0 (`solution/server.py:128-129`) and scores 0. No organizer submission shows that a score above 0 is reachable.

**Fairness verdict: unfair.** The problem is measurement, not vendor bias. The floor is parity with a same-compute opponent, so nearly every submission clamps to 0, and the non-zero scores (≤11.9) are separated by 1-2 SE. Placements on this task are mostly noise.
