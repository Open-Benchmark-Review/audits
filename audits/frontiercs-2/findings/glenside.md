# glenside

**Verdict:** `glenside: CONSTRUCT (UNCONFIRMED), MINOR`. Affected runs: none flip on a confirmed defect. All 12 passes rely on the same permitted move: pruning the generic exploration rule.

## How it's scored
- 14 held-out convolution and concat workloads.
- `im2col_discovery`: cand >= ref.
- `rewrite_time_seconds` (median of 3 `Runner.report().total_time`): cand <= ref, no tolerance.
- `egraph_node_growth` (max of 3): cand <= ref.
- PASS is the conjunction over all workloads (judge/beat_spec.json).

## P(reference passes vs itself)
- Very small. Discovery and node growth tie and pass, but time must be <= ref on all 14 workloads: about 0.5^14 ≈ 6e-5 if the workloads are independent.
- Empirical check: muse changed only the analysis (score 82.88 vs ref 82.88) and passed 10/14 time checks, which implies about (10/14)^14 ≈ 0.9%.
- The in-run reference score sd is 0.06 (82.70–82.90), so the measurement is stable.

## Findings
1. **CONSTRUCT (UNCONFIRMED). The passes come from disabling or narrowing upstream's generic `flatten-unflatten-all-accesses` rule and fusing a targeted dot-product rewrite.**
   - k31 replaces the rule with a no-op `(access-pair ?l ?r) => (access-pair ?l ?r)` (k31.patch:35-38).
   - opus uses `never_fires`, gemini uses `NoOpSearcher/NoOpApplier`, and terra uses a no-op on `access-shift-right`.
   - The others restrict it with conditions (`flatten_useful`, `can_flatten_item`, and similar). The no-op cases also neutralize `bubble_reshape_through_cartesian_product`.
   - The fused rule (for example k31's `bubble_reshape_through_compute_dot_product` applier) builds `reshape(compute dot-product(cartprod(flatten l, flatten r)))` directly. That is exactly the form the fixed systolic mapper needs.
   - The README explicitly allows "Legal compact or fused generic implementations ... no hook must fire" (judge/readme Interface §Generic rewrite constructors) and forbids only "dedicated convolution lowering". So this is within the rules.
   - The paper's claim is that *generic* rewrites discover im2col. Beating it by removing the generic exploration measures rule targeting, not a better access-pattern rewriting method. I have not marked this egregious, because the fused rule is not convolution-specific.
2. **MINOR.** The 0.0-score runs failed private guards. k27 and qwen got "candidate analysis contract failed" on every call. step got "generic rewrites cannot construct accelerator or opaque calls". The README documents both guards in detail. I did not find a hidden requirement, but I did not audit judge/analysis_contract.rs (255 lines) case by case. ds1017 got agent_job_failed from a workspace volume limit, which is infrastructure or agent-side.
3. **Consistency.** Superseded runs on 10-10 (in other_runs) predate the formal runs on 10-11 onward. The formal reference score is stable across all of them.

## Passing runs checked (12)
- I spot-checked how each passing patch changed `flatten_unflatten_any_access`: sol, ds, k3, glm, astra, opus, wonder, glmf, gemini, gemini-agy, terra, k31.
- None reads files or env, hard-codes workloads, or constructs accelerator nodes. The judge guards against the last of these, and step was rejected by that guard.
- All 12 are legit under the stated rules. They share the construct caveat in Finding 1.

## Notes
- The no-tolerance time gate would be FN-prone for small improvements, but every passer had a large margin (score about 90–91 vs 82.8).
