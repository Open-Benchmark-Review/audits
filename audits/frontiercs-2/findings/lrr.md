# lrr

**Verdict:** `lrr: MINOR (CONFIRMED: small measurement nondeterminism; RLI zero placeholder) — no pass/fail flip`
Affected runs: none. 0/17 PASS. No run is within one flip of passing.

## How it's scored
- `judge/beat_spec.json`: 4 workloads (dev / held-out × RegexScalpel-eliminated / unresolved; 10, 10, 40, 40 regexes) × 8 metrics.
- Each cell is a strict improvement over the reference prompt policy: VER, repair, well-formed, NLS, Jaccard, precision and recall must be higher (equality allowed only at 1.0), and RLI must be lower. 32-cell conjunction.
- The LLM (Qwen3-8B Q4_K_M on an L4) is the **system under test**, driven by the submitted prompt policy. It is **not a judge**. Metrics come from deterministic scripts: ReDoSHunter, edit distance, and Xeger sampling.

## P(reference passes vs itself)
0. Strict comparisons on every cell.

## Findings

### 1. Stochasticity (CONFIRMED small, MINOR)
- Decoding is greedy with seed 42 (`judge/evaluator.py:147`). Xeger uses `seed=42` (`judge/judge_assets/run_xeger.py:59`).
- The remaining variability sources are the 60 s ReDoSHunter wall-clock timeout (`evaluator.py:203`; timeouts count as failures) and CUDA/llama.cpp kernel nondeterminism. The README admits "timeout-based detection can still vary".
- The reference is re-measured in every run: fidelity score 9.70 in 15 runs, 10.65 in 2 (qwen, ds1017). So the reference output is stable in about 88% of runs and differs by roughly one item otherwise.
- With 10-item dev workloads, one flip moves a rate by 0.1, which can matter for a strict gate. But the closest run, **terra** (score 39.0), fails 3 cells: VER and repair on dev-unresolved, and well-formed on held-out-eliminated. ds1017 (score 74.0) fails NLS on all 4 workloads plus 5 more cells, a real safety-vs-similarity trade-off. No verdict is noise-decided.

### 2. MINOR: RLI zero placeholder
- Invalid outputs get RLI 0, so `rli` cleared 4/4 for every run, including astra with score 0.
- This can't flip pass/fail on its own because the well-formed and NLS gates catch invalid outputs. It does mean the `rli` cell carries no information for broken policies.

### 3. Infrastructure
- k31's own final verification failed (GPU runner HTTP 502). A recovery run re-scored the identical payload (`result_note`), and it FAILed on merits.
- k27 timed out and k3 exited without a final submission. Both agent-side.

### 4. Achievability (OK)
- No run passes, but terra satisfies 29/32 cells and the cells are individually achievable: VER/repair is achieved by several runs on other workloads, and NLS/RLI by terra.
- There's a real tension between edit-minimality (NLS/RLI) and safety (VER/repair), but nothing suggests the gate is unreachable.
- The judge comments say "Full-scale runtime qualification is pending" and that the detector is a "disclosed reconstruction". Both are disclosed.

## Passing runs checked
None.

## Notes
Hack surfaces: only the prompt renderer/templates are editable, the model and decoding are fixed, and the held-out regexes aren't in the agent image. No suspicious score jumps among FAILs; ds1017's high score comes with large RLI and low NLS, consistent with aggressive rewriting.
