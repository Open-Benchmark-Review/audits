# evm_state_checkpoints: FP (CONFIRMED surface pre-fix; opus PASS not shown to depend on it) + benchmark inconsistency (CONFIRMED) + FN (UNCONFIRMED). Affected runs: opus (caveat only), all 17 (version split)

## How it's scored
- Pre-fix (14 formal runs, 3 final workloads), per workload:
  - correctness,
  - Spectrum committed_tps: min(cand 5) > max(ref 5),
  - micro-trace create_ns, restore_ns and retained_bytes: max(cand 5) < min(ref 5) (`git show 9ea965c7^:.../judge/evaluator.py:203-223`).
- In the pre-fix micro trace, TPS came only from Spectrum, while create/restore/bytes came only from the `checkpoint_bench.cpp` trace at height 1000.
- Post-fix (gemini-agy, terra, k31): 6 workloads, and every workload reports all five metrics.

## P(reference passes vs itself)
- Strict range separation of 5 vs 5 gives 1/252 per timing metric.
- retained_bytes is deterministic, so equality fails it.
- Result: P about 0.

## Findings
1. **FP surface pre-fix (CONFIRMED by the developers in 9ea965c7).**
   - In the pre-fix `checkpoint_bench.cpp`, only `save_checkpoint()+push_back` (lines 110-114) and the first `load_checkpoint()` (131-134) were timed.
   - The post-checkpoint `get_mut` writes (115-120) and the post-restore `get()` checks (136-146) were untimed. Spectrum timed neither create nor restore.
   - So a backend could take one code path in Spectrum and a different, lazier one at height 1000. The commit names a Gemini final doing exactly this. It was the pre-fix gemini-agy attempt (other_runs 10-25 03:37, PASS 100), not accepted; the formal gemini-agy is a fresh run on the revised task.
2. **opus PASS (pre-fix, 88.53): structurally similar, but not shown to depend on it.**
   - The final patch keys behaviour on stack height (`opus.patch:48` `flat_max = 63`):
     - shallow stacks get an eager flat heap copy on save/restore (`:871-881`, `:910-916`);
     - deep stacks get O(1) page-table sharing, a "pending" refcount committed on the next mutation (`:882-889`), and an O(1) restore pointer swap (`:896-908`) whose table copy (`unshare`, `:325-343`) is deferred to the first write.
   - The pre-fix trace never writes after restore, so that deferred cost was never timed. Its trace restore_ns was 25 ns.
   - The opus trace (`traces/evm_state_checkpoints/opus`) shows it measured Spectrum `maxh=25/17` and added the ≤63 split "to avoid copy-on-write" for TPS, "keeping O(1) sharing for large stacks… trace still uses O(1) sharing".
   - But its earlier v2, a uniform paged COW with no height split, already scored 88.23 and passed 5/5 metrics on 2/2 dev workloads (verification_01M4QPPKQTHY6RJC2YASD8WZVX).
   - O(1) COW create/restore is the paper's design. The reference also defers slice copies to `get_mut` (`judge/reference.patch` `ensure()`), and post-fix create/restore definitions are unchanged.
   - Verdict: legit COW design. Whether it would still pass post-fix (Spectrum-side create/restore/bytes, plus the access-mix throughput) is UNCONFIRMED, since I did not execute the patch.
3. **Benchmark inconsistency (CONFIRMED).**
   - 14 formal runs (10-07..10-24) were scored on the 3-workload pre-fix version, with ref score 58.6–61.8.
   - gemini-agy (10-25 23:06, note "Rerun on revised task"), terra (10-26) and k31 (10-26) were scored post-fix: 6 workloads, `workload_cases: 6`, ref 74.5–76.1.
   - The jump of about 61 → 75 comes from the redefined composite (per-workload geomean over all metrics) and the shipped-backend anchor quality (about 95 → 74). It does not reflect a reference change: `reference.patch` is untouched by 9ea965c7.
   - Pass/fail standards therefore differ across runs: opus passed the old rule, gemini-agy the new one.
4. **FN risk on committed_tps (UNCONFIRMED).**
   - The 1-s Spectrum TPS runs use strict 5-vs-5 separation. The margins sit at the noise level: glm 47.9k passed 2/3, opus 48.1k passed 3/3, astra 46.4k passed 1/3.
   - In opus's own dev runs, TPS flipped to 1/2 between near-identical variants.
   - astra, sol and wonder fail only (or mainly) on TPS.

## Passing runs checked
- opus: legit COW (caveat above).
- gemini-agy: post-fix rerun; scored under the fixed harness, not examined for the old loophole.

## Notes
- `shipped_backend_quality` (the live anchor) ranges from 49.9 (ds) to 96.9. The continuous score is noisy, but beats_reference doesn't use it.
