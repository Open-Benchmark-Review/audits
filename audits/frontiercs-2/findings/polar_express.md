# polar_express

**Verdict:** `polar_express: CONSTRUCT, FP (CONFIRMED by simulation); MINOR (workload-keyed coefficients)`. Affected runs: all 14 PASS runs (glm, astra, sol, ds, k3, muse, opus, wonder, qwen, gemini, ds1017, gemini-agy, terra, k31). They are legitimate engineering, but the PASS flag does not show that anyone beat the paper's method.

## How it's scored
- `judge/evaluator.py:612-623`: on all 12 workloads (6 small, 6 paper-regime), the candidate must be strictly better than the reference on 5 metrics: scalar sup-error, relative-Frobenius, spectral, top-subspace (all `<`), and cosine (`>`). That is 60 strict comparisons.
- The bar (`_stricter_bar`, `evaluator.py:552-565`) takes, per metric, the better of the published bf16 reference and the same source with the cast changed to fp32 (`evaluator.py:520-521`).
- Everything is deterministic (fixed seeds, 1 thread). Reference score is 26.335 in all 15 runs, stdev 0.

## P(reference passes vs itself)
**0.** The runs are deterministic and the rule is strict, so a copy of the reference ties every comparison and fails.

## Findings
1. **The scalar metric is won by deleting the paper's safeguards (CONSTRUCT, CONFIRMED).**
   - The evaluator passes each workload's `safety_factor_eps` and `cushion` into `optimal_composition` (`evaluator.py:328-331`), then scores the pure sup-error on `[l,1]` (`evaluator.py:458-464`).
   - The upstream composition (`judge/reference.patch:51-77`) deliberately trades exact-arithmetic error for bf16 robustness: a 1.01 safety rescale and cushioning.
   - Simply ignoring those two arguments (the paper's plain greedy Remez) beats the reference on 12/12 workloads. Computed with the reference's own `optimal_quintic` in numpy (`$SCRATCH/tools_mlrob/polar/sim.py`). Examples:
     - l=0.01, T=5: 1.23e-6 vs 3.60e-6
     - l=0.001, T=6: 9.2e-4 vs 1.7e-3
     - l=0.12, T=3: 3.83e-5 vs 4.20e-5
   - The README calls these parameters "safeguard parameters" but never requires honouring them (`agent-base/frontier/task/repo/README.md`, Interface section).
2. **The matrix metrics are won by a trivial re-parameterisation of the reference (FP, CONFIRMED by simulation).**
   - The candidate is the reference `PolarExpress` code with:
     - fp32 precision;
     - greedy coefficients with no safety factor or cushion;
     - no 1.01 Frobenius inflation;
     - on the 6 small workloads, `l` set to the workload's published value. Spectra there are `geomspace(l,1,k)` (`evaluator.py:390`), and l is identifiable from (shape, steps, batch index) in the public table.
   - This candidate beats the fp32 reference on all 4 matrix metrics in 50/50 small-suite seeds and 30/30 paper-regime seeds. Numpy fp32 emulation of the evaluator's suite generator: `$SCRATCH/tools_mlrob/polar/{mat.py,small.py}`.
   - Keeping the 1.01 inflation still wins 30/30 on the paper regime.
   - Without workload-specific `l`, the same ablation loses (0/50 small-suite seeds; wide_0 polar 0.75 vs 0.52; `small2.py`). So PASS reduces to "use the stated sigma_min, drop bf16 margins". It does not require going beyond the paper.
   - The beat_spec v3 comment (`judge/beat_spec.json` comments) admits that v2 was cleared by "any tailored float32 implementation" and that "the six small workloads reveal their spectrum through (shape, steps)". v3 kept those six workloads unchanged.
3. **float64 execution is allowed (MINOR, CONFIRMED).**
   - The op guard allows `aten._to_copy` (`evaluator.py:308-313`). Patches compute in float64 (k31.patch: `X = G.double()`; gemini.patch: `G.to(torch.float64)`). The reference runs in bf16/fp32.
   - The README permits dtype conversion, so this is not a rule violation. It is extra headroom against an fp32 bar.
4. **Workload recognition (MINOR, CONFIRMED).**
   - The README says "The cases are representative generated numerical inputs, not values to recognise". Even so, several passing patches hard-code per-(steps, shape, member) schedules:
     - k31.patch `_original_matrix_coefficients` keyed `(3,10,18)`, `(4,18,10)`, `(5,12,12)`;
     - glm.patch:677-704 `_ORIGINAL_PAIRS` steps→(l0,l1);
     - gemini.patch key=(m,n,steps).
   - These use only public table values, so this is not a data leak.
5. Hidden-data leak: none found. Seeds and oracles live only in the verifier-side evaluator (`agent-base/Dockerfile` copies only `agent-base/frontier/task`).

## Passing runs checked (patch scan of all 17; 5 read in detail)
- k31: legit, but shape-keyed. Remez/greedy without safety; per-workload fp64 schedules with history terms; paper-regime = plain Frobenius normalisation + `optimal_composition(0.001, steps)`, which is exactly finding 2.
- gemini: legit. fp64 "history" schedules solved per (l0, l1), keyed by (m, n, steps).
- glm: legit. Remez plus per-steps l-pair tables (glm.patch:677-772).
- sol and astra: legit. Adaptive normalisation using `||X^T X||_F`-type bounds (sol.patch:137-160), longdouble Remez, no workload table found.
- opus: legit. Batched Remez composition evaluated in double, multi-degree steps.
- Remaining passes: same family (Remez without safety, fp64, tailored l). No reflection, file access or reference leakage.
- FAIL runs: k27 and glmf scored 0 (invalid submission); step passed only 6/12 workloads.

## Notes
- No reference-score jumps: the reference score was identical in all 15 runs. One commit only (a56a2afa).
- A 14/17 pass rate shows the bar measures "noticed the regime mismatch" (fp32/fp64 CPU, known spectra, safeguards penalised) rather than "beat Polar Express".
