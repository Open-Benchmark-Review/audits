# bbq_packet_scheduling

**Verdict:** `bbq_packet_scheduling: OK, CONSTRUCT-minor (UNCONFIRMED)`. Affected runs: none. All 5 PASSes look legitimate.

## How it's scored
- 9 final workloads: 4 public dev traces rerun, 4 hidden seeds on the same configs, and 1 hidden configuration (`hidden_scale`, depth 3, width 16, capacity 255) (judge/evaluator.py:28-31).
- Throughput is `count/(cycles*period_ps)`, with cand > ref **strictly**.
- Worst latency is `cycles*period_ps`, with cand <= ref. Both use exact integer cross-multiplication (evaluator.py:58-62).
- The period comes from sv2v + Yosys `synth -flatten` + a fixed ABC LUT6 script, under a unit-delay model with no placement or routing (harbor/app/frontier_cpu/timing.py).

## Is synthesis deterministic? P(reference passes vs itself)
- **Deterministic (CONFIRMED empirically).** 78 train-evaluation evidence files across 16 runs contain a single distinct reference resource row (period_ps 2800/2800/2800/3300 ps on dev_a–d, identical LUT and register counts) and a single reference score, 26.701694726.
- The final in-run reference score is identical (25.99641787) in all 16 formal runs (sd 0).
- Yosys runs under YoWASP (WASM) with a fixed script and no seed. Cycles come from the Verilator simulation.
- **P(reference passes vs itself) = 0**, because the throughput check is strict and equality fails.

## Findings
1. **CONSTRUCT-minor (UNCONFIRMED). Area is not charged.**
   - Resource counts are "operator-only diagnostics" (beat_spec.json comments). sol and opus use about 10x the reference LUTs on dev_d (12,060 and 12,888 vs 1,146) and about 3.5–4.5x the registers to reach a 1800 ps period vs 3300.
   - The paper's fmax/resource tradeoff is therefore one-sided. This is disclosed and does not flip any verdict, since gemini, gemini-agy and terra pass with roughly reference-level area.
2. **Timing-model gaming surface: not found.** The simulated RTL and the synthesized RTL are the same file, and their hashes are logged in evidence (evaluator.py `_build_evidence`).
   - The design rules ban latches, extra memories, async or negedge registers, and multiple drivers.
   - I grepped the passing patches for seed literals, `public_cases`, env, file or `os` access, and references to `timing.py`. None found.
3. **Consistency.** The task changed between 10-13 and 10-14: other_runs on 10-06 to 10-13 include many PASSes at scores up to 71.77 under an older spec. All formal runs are on 10-14 or later with one fixed reference (25.996), so the formal results are consistent.
   - k27 TIMED_OUT (agent deadline).
   - qwen, glm and step scored 0 or 0/9, which is candidate-side.

## Passing runs checked (5)
| model | dev period (cand vs ref) | LUTs dev_d | verdict |
|---|---|---|---|
| sol | 1800–2300 vs 2800–3300 | 12,060 | legit (bit-sliced counters, registered resolution, RAM prefetch helpers) |
| opus | 1800 all vs 2800–3300 | 12,888 | legit (rewritten LX level, wide parallel logic) |
| gemini | 1800–2300 | 1,105 | legit (combinational waterlevel counter restructure) |
| gemini-agy | 1800–2300 | 1,281 | legit |
| terra | 2800 (dev_d 2800 vs 3300) | 774 | legit (fewer LUTs; wins on cycles and dev_d period; small margin 27.03 vs 26.00, but deterministic) |

All 5 pass 9/9 on both metrics, including the hidden-scale configuration, which argues against config overfitting.
