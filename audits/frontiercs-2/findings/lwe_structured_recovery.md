# lwe_structured_recovery

**Verdict:** `lwe_structured_recovery: IMPOSSIBLE (CONFIRMED, empirical + attack-cost estimate); CONSTRUCT/MINOR (no held-out set, empty reference; disclosed)`
Affected runs: all 17 (0 PASS). Pass/fail is unreachable, so the task contributes a guaranteed 0 to every model's pass rate.

## How it's scored
- `judge/beat_spec.json`: one workload per public instance (200), metric `valid_witness` ∈ {0,1}. A cell clears when candidate > reference. The reference is the **empty ledger** (`judge/reference.json` = `{"schema_version":1,"solutions":[]}`), so PASS ⇔ **all 200 instances solved** (`repo/README.md:286-290`).
- Continuous score = 100 · solved/200 (reference-independent). Train and final use the same public catalog with no hidden split (paper Appendix A: "its final suite has no held-out part").

## P(reference passes vs itself)
0. Empty ledger, strict `>`.

## Findings

### 1. IMPOSSIBLE (CONFIRMED): 32 instances unsolved by every model; attack cost far beyond budget
- I downloaded all 15 final patches and validated them with the repo's own `lwe_instance.validate_secret` (`$SCRATCH/r6/lwe_union.py`). My counts reproduce the judge's exactly: astra 168, terra 168, sol 161, wonder 158, k31 153, opus 144, ds 140, muse 140, ds1017 135, glm/glmf/qwen 116, step 100, gemini-agy 28, k3 19.
- **The union over all runs is 168**, the same as the best single run. The same 32 IDs are never solved:
  - `lwe_0013–0016`: dense uniform A, binary weight-14 secret, n=120–150, m=n+8, q=257, error uniform in [−32,32].
  - `lwe_0027–0040`: same shape, balanced ternary weight-14 secret, n=75–135.
  - `lwe_0047–0060`: dense uniform A, **dense iid binary secret**, n=70–88, m=n+8, q∈{257…4093}, error uniform in ±q/8.
- Primal-uSVP block-size estimate (2016 estimate, optimal sample count; `$SCRATCH/r6/lwe_beta.py`): every unsolved instance needs **β ≈ 112–176**.
  - The dense binary family (0047–0060), with no sparsity to exploit, needs β ≈ 114–143.
  - With only `fplll-tools` (README "Resources"; no G6K/GPU), 8 CPUs and 5 h, BKZ/enumeration at β > 110 is many orders of magnitude out of reach (one SVP-110 enumeration is on the order of 2^45 nodes).
  - Solved weight-14 binary instances (0007–0012, 0017–0020, n=80–110) also have high primal β, but fall to combinatorial/hybrid attacks thanks to the sparse binary secret. The ternary and dense variants don't.
- So the "solve all 200" gate is not achievable within the task's resources. It's also impossible to *prove* infeasibility; the evidence is 0/15 independent attempts on 32 instances plus the cost estimate.

### 2. CONSTRUCT / MINOR: degenerate "beat the reference"
- There is no paper code being reconstructed. The task is an original challenge (paper Appendix A; metadata cites Jain–Lin–Saha "A Systematic Study of Sparse LWE"). "Beat the human reference" reduces to "solve every instance".
- No held-out set, so training on the final suite is by design. This is disclosed and harmless here because witnesses are publicly verifiable and can't be faked (the checker reconstructs A from SHAKE seeds and checks only public predicates).

### 3. FP surfaces checked, none found
No planted witness or private seed is shipped (README "Reproducibility"). Acceptance is purely mathematical, so a submitted secret either satisfies the predicates or doesn't.

## Passing runs checked
None (0 PASS). The top runs' witnesses validate locally.

## Notes
- Scoring is correct and deterministic: reference score 0.0 in all runs, and my local re-validation matched the judge counts exactly.
- glm, glmf and qwen each solved exactly 116 (glm and glmf patches are the same size). Possibly the same solved set; not investigated further.
