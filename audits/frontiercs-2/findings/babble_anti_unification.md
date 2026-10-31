# babble_anti_unification

**Verdict:** `babble_anti_unification: MINOR (CONFIRMED)`. Affected runs: none. The one PASS (opus) is legitimate. Every FAIL fails the deterministic compression gate.

## How it's scored
- 10 final DreamCoder corpora (2 per domain).
- `compression_ratio`: cand >= ref − 1e-12. This is deterministic, and the evaluator rejects unstable discrete outputs across 3 repetitions.
- `runtime_seconds`: median of 3 runs, cand < ref strictly, on every workload (judge/evaluator.py:377-419).
- Reference observations are measured **once and cached** at judge startup (`_REFERENCE_CACHE`, evaluator.py:439-466). They are not paired or interleaved with the candidate.

## P(reference passes vs itself)
About 0. When the candidate is the reference, the evaluator reuses the reference observations (evaluator.py:487-491), so the strict runtime check fails on equality. An independent re-measurement would pass strict `<` on all 10 with about 0.5^10 ≈ 0.1% probability.

## Findings
1. **MINOR (CONFIRMED). Runtime gate noise is large, but it decided no observed verdict.**
   - The same opus patch (dev score 22.923) gave runtime wins of 5/5, 2/5, then 5/5 on consecutive train calls. corpus-2 took 0.54, 1.88 and 0.57 s (trace verifications).
   - The implied reference total varies 2.72–3.29 s across calls.
   - Because the reference is cached and unpaired, machine-state changes hit only the candidate side.
   - In the finals, every FAIL also fails compression on at least one workload (checks: compression 2–9/10). The runtime gate therefore never flipped a verdict, and opus passed despite the noise.
2. **MINOR.** config.yaml lists `max_dev_submissions: 3`, while policy.json allows 100 train calls. Runs used up to 12, so the effective limit is 100. This is a documentation inconsistency only.
3. **Construct: OK.** Compression ties pass, so a pass needs >= reference compression on every corpus plus a speedup. Most candidates with higher *mean* compression (ds 19.35, glmf 19.11, terra 18.98, sol 18.94) fail on at least one corpus. That is by design: per-workload non-inferiority.
4. **Consistency.** The reference score is identical (18.8434) across all 16 scored runs. ds1017 had agent_job_failed and no patch.

## Passing runs checked
- **opus → legit.** The patch (src/dfta.rs, src/learn.rs inside the edit regions) re-implements anti-unification candidate generation with hash-consed terms, dense e-class numbering and memoised paired-state sets. Comments note it follows "the depth-first order of the product-automaton enumeration exactly" and keeps `deduplicate`'s tie-break.
- Its compression ties or slightly beats the reference on all 10 corpora (score 18.890 vs 18.843). Runtime is about 2x faster (dev aggregate 1.33 s vs about 2.85 s).
- The forbidden list (`std::time`, `std::fs`, `std::env`, and others; evaluator.py:71-76) blocks timer tampering. Runtime is measured in fixed upstream `experiments.rs`.

## Notes
- If this task ever adds runtime-only winners, the unpaired, cached reference plus a strict per-workload `<` will produce FN/FP flips. Pairing or interleaving the reference would fix it.
