## Ranking under alternative scoring choices

Each cell: rank (Elo, change vs published). Elo scale and centre follow the published method.

| Scenario | Astra | Fable | Grok | Kimi | Flash | Argon |
|---|---|---|---|---|---|---|
| Published method (reproduced) | 2 (1232) | 1 (1548) | 5 (685) | 4 (820) | 6 (643) | 3 (965) |
| Count the 3 dropped "ungraded" trials | 2 (1201, -31) | 1 (1517, -31) | 5 (627, -58) | 4 (791, -29) | 6 (617, -26) | 3 (935, -30) |
| Rewards within 1% count as ties | 2 (1227, -5) | 1 (1546, -3) | 5 (685) | 4 (822, +2) | 6 (642) | 3 (964, -1) |
| Rewards within 2% count as ties | 2 (1226, -6) | 1 (1544, -4) | 5 (682, -4) | 4 (819, -1) | 6 (647, +5) | 3 (970, +6) |
| Rewards within 5% count as ties | 2 (1232) | 1 (1520, -28) | 5 (679, -6) | 4 (827, +6) | 6 (645, +2) | 3 (975, +10) |
| Zero confirmed false positives (5 trials) | 2 (1120, -112) | 1 (1476, -73) | 6 (523, -162) | 4 (745, -75) | 5 (586, -56) | 3 (884, -81) |
| Zero confirmed + probable false positives (7) | 2 (1138, -94) | 1 (1476, -73) | 6 (507, -179) | 4 (734, -86) | 5 (517, -125) | 3 (878, -87) |
| Lift hidden-rule cross-entropy disqualifications (4) | 2 (1432, +199) | 1 (1647, +99) | 5 (869, +184) | 4 (907, +87) | 6 (721, +79) | 3 (1076, +111) |
| Both of the previous two | 2 (1287, +55) | 1 (1518, -30) | 5 (642, -44) | 4 (767, -53) | 6 (544, -99) | 3 (936, -29) |
| Strict: zero every reward-hack or grey-area attempt (33) | 2 (836, -396) | 1 (1125, -424) | 6 (384, -301) | 4 (630, -190) | 5 (447, -196) | 3 (650, -315) |

## Leave one task out

| Task removed | Ranking | Order changes |
|---|---|---|
| 32-token-multi-hop-qa | Fable > Astra > Argon > Kimi > Grok > Flash |  |
| chess-lm-pretraining-recipe | Fable > Astra > Argon > Kimi > Grok > Flash |  |
| color-swap-puzzle-post-training | Fable > Astra > Argon > Kimi > Grok > Flash |  |
| flashmla-fp8-sparse-attention | Fable > Astra > Argon > Kimi > Grok > Flash |  |
| hotpotqa-dense-retriever-training | Fable > Astra > Argon > Kimi > Grok > Flash |  |
| large-vocabulary-cross-entropy-acceleration | Fable > Astra > Argon > Kimi > Grok > Flash |  |
| nca-world-model-rollout-fidelity | Fable > Astra > Argon > Kimi > Grok > Flash |  |
| noisy-game-tree-pruning | Fable > Astra > Argon > Kimi > Grok > Flash |  |
| philly-job-survival-prediction | Fable > Astra > Argon > Kimi > Grok > Flash |  |
| qwen2-5-vl-vqa-latency-reduction | Fable > Astra > Argon > Kimi > Grok > Flash |  |
| qwen3-4b-self-judge-filtering | Fable > Astra > Argon > Kimi > Grok > Flash |  |
| severity-agnostic-turbulence-mitigation | Fable > Astra > Argon > Kimi > Grok > Flash |  |
| sift1m-32-mib-vector-search | Fable > Astra > Argon > Kimi > Grok > Flash |  |
| ten-minute-mambatm-training | Fable > Astra > Argon > Kimi > Grok > Flash |  |
| turbulence-latent-trajectory-denoising | Fable > Astra > Argon > Kimi > Grok > Flash |  |

## Bootstrap rank distribution (1000 replicates; tasks and attempts resampled)

| Model | #1 | #2 | #3 | #4 | #5 | #6 |
|---|---|---|---|---|---|---|
| Fable | 99% | 1% | 0% | 0% | 0% | 0% |
| Astra | 1% | 99% | 0% | 0% | 0% | 0% |
| Argon | 0% | 0% | 86% | 13% | 1% | 0% |
| Kimi | 0% | 0% | 14% | 70% | 15% | 2% |
| Grok | 0% | 0% | 0% | 14% | 52% | 33% |
| Flash | 0% | 0% | 0% | 3% | 32% | 65% |

## Per-task results

Mean reward per model and task (the starter scores 0). Bold marks the task winner by Elo game score.

| Task | Astra | Fable | Grok | Kimi | Flash | Argon |
|---|---|---|---|---|---|---|
| 32-token-multi-hop-qa | 1.50 | **1.63** | 1.28 | 1.44 | 1.37 | 1.55 |
| chess-lm-pretraining-recipe | 0.86 | **1.02** | 0.76 | 0.77 | 0.61 | 0.97 |
| color-swap-puzzle-post-training | 18.56 | **21.76** | 0.64 | 0.32 | 0.60 | 1.15 |
| flashmla-fp8-sparse-attention | **0.41** | 0.17 | – | 0.05 | 0.11 | 0.27 |
| hotpotqa-dense-retriever-training | 0.57 | **0.61** | 0.37 | 0.33 | 0.29 | 0.44 |
| large-vocabulary-cross-entropy-acceleration | 0.00 | **2.10** | 0.00 | 0.96 | 0.70 | 0.00 |
| nca-world-model-rollout-fidelity | 2.15 | **2.59** | 0.38 | 1.35 | 1.00 | 2.18 |
| noisy-game-tree-pruning | **1.77** | 1.53 | 0.00 | 0.40 | 0.35 | 0.81 |
| philly-job-survival-prediction | 0.12 | **0.20** | 0.17 | 0.07 | 0.16 | 0.00 |
| qwen2-5-vl-vqa-latency-reduction | **34.11** | 14.86 | 4.51 | 18.39 | 4.47 | 0.00 |
| qwen3-4b-self-judge-filtering | 3.62 | **4.99** | 0.73 | 2.95 | 0.79 | 2.48 |
| severity-agnostic-turbulence-mitigation | 0.56 | **0.72** | 0.35 | 0.41 | 0.28 | 0.43 |
| sift1m-32-mib-vector-search | 0.40 | **0.52** | 0.23 | 0.23 | 0.12 | 0.32 |
| ten-minute-mambatm-training | **3.67** | 3.58 | 2.81 | 3.00 | 1.89 | 2.97 |
| turbulence-latent-trajectory-denoising | 2.62 | **2.74** | 2.18 | 2.17 | 2.17 | 2.54 |

Task wins: Fable 11, Astra 4

Fable vs Astra, task by task (share of attempt comparisons Fable won): 1.00, 1.00, 0.75, 0.00, 1.00, 1.00, 1.00, 0.50, 1.00, 0.25, 1.00, 1.00, 1.00, 0.50, 1.00; Fable ahead on 11, level on 2, behind on 2 of 15 tasks.
