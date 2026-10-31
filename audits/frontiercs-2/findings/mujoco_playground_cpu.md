# mujoco_playground_cpu

**Verdict:** `mujoco_playground_cpu: MINOR; FN (UNCONFIRMED)`. Affected runs: none confirmed. gemini and ds1017 were infrastructure or no-final failures with no patch (`agent_job_failed`).

## How it's scored
- The candidate and the shipped PPO config (200M steps, about 450 s) are each trained once per training seed on the same H100, under a 720 s wall budget (`judge/judge_deps/workloads.json`: `train_budget_seconds` 720).
- Final has 5 training seeds × 3 conditions (flat, push, rough) = 15 workloads.
- On each workload, the candidate must be strictly better than the reference on episode_reward, tracking_lin_vel, tracking_ang_vel, energy (per alive step) and action_rate (per alive step). That is 75 strict comparisons (`judge/beat_spec.json` "beats_reference").
- Score = 100·r/(r+30).

## P(reference passes vs itself)
**About 3e-4 to 3% (author-measured; CONFIRMED); below threshold.**
- The beat_spec comments report a reference-vs-itself final suite: "one of five training pairs had the candidate ahead on all 15 comparisons, none had it behind on all 15, four were mixed".
- The author bounds the false-pass rate between (1/5)^5 and (1/2)^5, and chose 5 seeds for that reason.
- Development reference-vs-itself lost all 10 comparisons.

## Findings
1. **No attainability witness and unknown per-step noise (FN, UNCONFIRMED).**
   - The beat_spec says: "Attainability: no witness exists ... the noise of the per-step metrics is unknown".
   - The metrics pull in different directions. Better tracking tends to cost energy and action_rate. Example: astra passed 15/15 on episode_reward, energy and tracking_ang_vel, 14/15 on lin_vel, but only 7/15 on action_rate.
   - Seed noise on episode_reward (sd 0.23–0.29 on about 30, author's runs) makes +1% improvements pass each comparison only about 80% of the time. Example: sol scored 49.93 vs 49.63 and passed 12/15 on episode_reward.
   - A real improvement of several sd on all five terms should pass, so this is a hard but valid bar rather than a confirmed FN.
2. **The extra wall budget is a free lever (MINOR/CONSTRUCT-lite, CONFIRMED).**
   - The reference uses about 445–464 s of the 720 s budget (beat_spec comments).
   - A candidate can train about 1.5x more steps, and the comment notes reward "still rises from 100M to 200M".
   - This is legitimate under a fixed wall-clock budget, but it partly reintroduces the "raise the step count" lever that the comment claims to remove.
3. **Train calls (MINOR, CONFIRMED).**
   - `max_train_calls` = 3, and each development verification takes about 1,100–1,900 s.
   - The agent has its own H100 allowance of 14,400 s (README, around line 284), enough for roughly 12–15 self-run trainings. So it is constraining but not crippling.
4. **Naming (MINOR).** The task is called `_cpu` but requires an H100 for both agent and verifier (`policy.json` accelerator `allowed_types` H100).
5. **Reward-hack surfaces (checked, none found).**
   - Both sides are evaluated with the hash-verified pristine environment code, the same eval seed and the same env count (beat_spec validity).
   - The reference is the visible shipped config ("Nothing has been removed", README line 14), so recovering it gives no advantage.

## Passing runs checked
None passed.

## Notes
- The reference score is stable (49.40–49.72, stdev 0.08), consistent with the author's noise numbers.
- An earlier verifier bug, a finite-action check on terminated envs that rejected the trusted reference, was fixed before the formal runs (beat_spec comments).
- Early other_runs (Oct 6–10) used a different scale (scores 16–50; astra "PASS" at 50.0), which fits the documented score-formula change. All formal runs are Oct 11 or later.
