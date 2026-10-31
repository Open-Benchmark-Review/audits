# AI4AI-Bench: evaluation setup audit

## Sources

- arXiv 2608.20318, Section 3 and Table 3
- [`Einsia/AI4AI-Bench`](https://github.com/Einsia/AI4AI-Bench) at `5ced1e2`, specifically `orchestrator/` and each
  task's `task.toml` and `declaration.py`
- the 290 case pages at lab.einsia.ai/ai4ai/trajectories/, parsed into [`data/cases.csv`](data/cases.csv)

## Budget for every cell

- 4 h Explore on one B300
- egress limited to the model API through an allowlisting proxy (`orchestrator/egress.py`)
- only the source patch crosses into a fresh Formal run of up to 12 h, with `network_mode = "no-network"`
- up to 3 checkpoints, each validated, then scored by the task's frozen evaluator
- the reported result is the best of the three on the final metric (`orchestrator/final_score.py:148`)
- one run per cell

## Per-system configuration

| Entry | Model ID | Harness and version | Reasoning effort | Max output tokens | Context window used | Temperature / sampling | Time, turn, and token budget | Tools and network | Retry and refusal policy | Attempts per task | Non-voluntary terminations | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Claude Opus 5 | `claude-opus-5` | Claude Code 2.1.220 | low, medium, high, xhigh, max (5 configurations) | undisclosed | undisclosed | undisclosed | 4 h Explore + 12 h Formal; no token cap | shell and file tools; model API only | Claude transport-retry hotfix applied mid-study (source waiver: replay commit `e2c7bd96` vs original `305d21c7`) | 1 per configuration | 0 | paper; case pages |
| Claude Sonnet 5 | `claude-sonnet-5` | Claude Code 2.1.220 | low … max (5) | undisclosed | undisclosed | undisclosed | same | same | same | 1 | 1 (Formal CUDA OOM, OpenR1 medium) | paper; case pages |
| Kimi K3 | `kimi-k3` | **Claude Code** 2.1.220 (not its own harness) | **max only** (1) | undisclosed | undisclosed | undisclosed | same; cost converted from CNY | same | same | 1 | 0 | paper |
| GPT-5.6 Sol | `gpt-5.6-sol` | codex-cli 0.146.0 | none … max (6) | undisclosed | undisclosed | undisclosed | same | same | Codex has no continuation: an early exit ends Explore | 1 | 2 (Formal failures) | paper; case pages |
| GPT-5.6 Terra | `gpt-5.6-terra` | codex-cli 0.146.0 | none … max (6) | undisclosed | undisclosed | undisclosed | same | same | same | 1 | **8** (three `agent_early_exit` at 93–99 s with ~4 h left, others with empty patches or failed Formal runs; one Formal run voided for GPU sharing) | case pages |
| GPT-5.6 Luna | `gpt-5.6-luna` | codex-cli 0.146.0 | none … max (6) | undisclosed | undisclosed | undisclosed | same | same | same | 1 | **8** (OOM, empty patch, failed publication) | case pages |

## Questions answered

- [x] **Equal budgets?** Yes: the same 4 h, 12 h and one B300 for every cell.
- [ ] **Same harness?** No. Codex for GPT-5.6 and Claude Code for Claude, which is disclosed. Kimi K3 runs in Claude
  Code rather than its own harness, at one effort level only.
- [ ] **Settings at the provider maximum?** By design, the study sweeps effort, including `none`. The headline
  "system" score averages over all levels, so systems with more weak configurations are penalised. Kimi K3, with
  only `max`, is not.
- [ ] **Same retry and refusal rules?** No. Codex runs end on an early exit, with no continuation. 18 of the 19
  zero-scored cells are Codex runs, several after under 100 s.
- [x] **Silent model switches?** None reported.
- [ ] **Re-runs and replacements:**
  - One DiGress Formal run was voided for GPU sharing and re-run.
  - Claude cells were replayed on a hotfix commit under a documented waiver.
  - A RAGEN Explore attempt was gate-only and repeated.
- [ ] **Same task version?** Mostly. OpenR1's final protocol changed on 2026-08-20 (greedy first-128 to full 175),
  and all cells were rescored. The public scorer does not reproduce the published n=10 numbers.
- [ ] **Attempts per task:** one per cell. Effort curves are non-monotone: Opus 5 scores 0.287 at medium and 0.188
  at xhigh. Gaps of about 0.1 σ between configurations are within noise.
- [x] **Modern harness?** Yes, the vendor CLIs.
- [x] **Network, and can the agent fetch the answer?** No network beyond the model API. The answer leaks found are
  inside the container: the RAGEN seed in upstream config, and the DDPO seed in harness source.
