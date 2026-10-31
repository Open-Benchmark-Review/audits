# diffusion_policy_cpu

**Verdict:** `diffusion_policy_cpu: FN (CONFIRMED)`. Affected runs: all 16 valid runs, and most clearly the 6 runs that cleared 3/4 workloads (glm, ds, qwen, gemini, step, k31). glmf was genuinely weak (0/4).

## How it's scored
- Push-T closed loop. The final suite has 4 groups (one env initial state each), each with 3 episodes under distinct diffusion seeds (`judge/trusted_workload.py:34`, `judge/measurement_contract.py:52-80`).
- Per group, the candidate needs:
  - mean episode-max reward Q `>=` reference;
  - success rate S `>=` reference, where S ∈ {0, 1/3, 2/3, 1};
  - mean predict_action latency L `<` reference;
  - workload wall time T `<` reference.
- Rule source: `judge/beat_spec.json` "beats_reference". The reference is the shipped 100-step DDPM sampler (`judge/reference.patch`).

## P(reference passes vs itself)
**About 1–6% (UNCONFIRMED); below threshold.**
- Quality ties exactly, since everything is seeded on CPU with 1 thread.
- Timing must be strictly lower in all 4 groups. With L and T strongly correlated and order alternated (`measurement_contract.py:77`), P ≈ 0.5^4 ≈ 6% at most, and about 0.4% if L and T were independent.

## Findings
1. **The quality gate is a coin flip for any faster sampler (FN, CONFIRMED from run data and structure).**
   - Being strictly faster is required, and the frozen transformer evaluation dominates cost. So any sampler that beats L and T must take fewer or different denoising steps, which yields different stochastic trajectories than the reference's seeded 100-step DDPM.
   - Q and S are then compared on 3 episodes per group with no tolerance. The beat_spec admits: "No repeated noise study exists ... Actual worker repeatability calibration remains a release prerequisite" (`judge/beat_spec.json` comments).
   - Run data: every valid candidate cleared timing on 4/4 workloads; `mean_predict_action_seconds` was 4/4 in all 17 runs.
   - The per-workload all-metric pass rate was 33/68 = 0.49 (passes per run: 3/4 ×6, 2/4 ×6, 1/4 ×3, 0 ×1).
   - That is what equal-quality samplers produce, and implies P(4/4) ≈ 0.49^4 ≈ 6% per run. P(0 of 17) ≈ 0.37, consistent with observed.
   - Candidates such as k31 are principled samplers: DPM-Solver++(2M), 11 steps, k31.patch. Their continuous scores (about 50–60 vs the reference's 11–18) show large speedups with Q well above the naive anchor.
   - The only route to a deterministic quality tie is a bit-exact replay of the reference's 100-step stochastic chain, run faster. That excludes the in-scope design space ("Denoising-step allocation ... in scope", README, Design space). It is also unlikely to beat timing noise strictly in every group.
2. **Unresolved spec conflict acknowledged by the author (MINOR, CONFIRMED).** The beat_spec comments say the cost metrics are "external instrumentation extensions" and "Author must resolve acceptance of these extensions before task release".
3. **Reward-hack surfaces (checked, none found).**
   - The sampler runs out-of-process through a bounded tensor protocol, with a 1–200 model-call bound and RNG-reseeding forbidden (README, Validity).
   - The patches read were plain samplers (k31; reference comparison).

## Passing runs checked
None passed.

## Notes
- Reference score varies 11.49–17.89 across runs (stdev 1.42). Cost measurement is noisy across hosts, but pairing within a run removes most of that.
- The train budget is 100 calls, so it is not constraining.
