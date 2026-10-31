# ragen_multi_turn_rl

**Verdict:** `ragen_multi_turn_rl: IMPOSSIBLE (practically), CONSTRUCT (CONFIRMED)`. Affected runs: all 17. qwen and step additionally failed with `agent_job_failed` and produced no patch.

## How it's scored
- The run is one PPO step (`train.py`, 6 groups × 4 trajectories of SimpleSokoban, 3 model turns, temperature 0.7, frozen Qwen2.5-0.5B).
- Final grades groups 1, 3, 5 with seed 314159 (`judge/evaluator.py:363-366`, `:339`).
- On each group, the candidate needs `success_rate >` the reference and `average_episodic_reward >` the reference (`evaluator.py:377-383`). That is 6 strict comparisons.
- Score = 10 + 60·mean(s) + 30·mean(clip((r+1)/12)).

## P(reference passes vs itself)
**0.**
- The rollouts are deterministic under the fixed seed: the reference score is 11.6875 in all 15 runs, stdev 0.
- glm, muse, k27 and ds1017 scored exactly 11.6875, i.e. they reproduced the reference rollouts, and failed on ties.

## Findings
1. **The score measures pre-update rollouts of a frozen model, so the editable code cannot express the paper's contribution (CONSTRUCT, CONFIRMED).**
   - The README says: "The scored rollouts occur before the optimizer calls. The single-step run ... does not measure a trained policy ... The fixed scheduler can use a zero learning rate" (`agent-base/frontier/task/repo/README.md`, Scoring).
   - The editable surface is only `ctx_manager.py` (trajectory/DataProto construction).
   - Prompts must contain the fixed instructions, the genuine observations and the genuine prior responses. Content may not be "invented, rewritten or supplemented". The only allowed choice is a contiguous history suffix (README, Model and trajectory provenance), and the action-provenance checker enforces this (`evaluator.py:262-270`).
   - Generation settings are fixed by the command line (`evaluator.py:37-58`).
   - The only lever on success or reward is therefore which suffix of at most 2 prior turns to show the model. Passing patches did exactly this:
     - sol.patch:89-95 `history_windows` → 0 or 1;
     - opus.patch:297-358 `select_history_windows`.
   - RAGEN's StarPO multi-turn RL training never affects the measured quantity.
2. **PASS is a lottery with negligible odds (IMPOSSIBLE in practice, CONFIRMED from run data).**
   - Reference final rollouts: 0 successes on all 3 graded groups. Mean episodic reward = (1.6875/30)·12 − 1 = −0.325.
   - A candidate must get at least 1 success out of 4 sampled trajectories on every graded group. The policy is a frozen 0.5B model at T=0.7, and the candidate can only change the context window.
   - 11 formal runs changed the rollouts (score ≠ 11.6875). Across 33 group draws, only 2 had success > 0: sol and opus, both 18.458 and both 1/3. That is about 6% per group, so P(all 3) ≈ 2e-4 per attempt.
   - The best achievable results were 1/3 groups on success and 2/3 on reward (gemini-agy).
   - No witness exists. The README itself says: "Earlier versions have measured GPU reference and solver results; those results do not establish acceptance or difficulty under this version's stronger model-provenance contract. Version-specific reference remeasurement is required."
3. **Tight agent budget (MINOR, CONFIRMED).** `max_train_calls` = 3. Agent debugging is limited to 1,800 A100-seconds (README, Resources).
4. **Infrastructure failures (FN-type, CONFIRMED but immaterial).**
   - qwen and step ended with `platform_state` FAILED and `failure_code` agent_job_failed, with no patch. Both are scored as FAIL.
   - Given finding 2 this cannot flip a verdict.

## Passing runs checked
None passed.

Consistency: two earlier non-accepted runs, astra and sol (Oct 10, other_runs), scored 98.9 and PASSED. That was before the "stronger model-provenance contract": the README now forbids "candidate-computed answers", which points to an earlier exploit (an injected planner) that was later closed. All 17 formal runs are Oct 11 or later, so they ran after the fix.

## Notes
- Correct reimplementations fail on exact ties (glm, muse, k27, ds1017). With a deterministic reference at 0% success, ties on success are the default outcome.
