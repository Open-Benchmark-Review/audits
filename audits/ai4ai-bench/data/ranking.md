# AI4AI-Bench ranking sensitivity

| Aggregation | System order (mean σ) |
|---|---|
| Published: mean over all effort levels, best-of-3 | Opus 5 (0.249) > Sol (0.190) > Kimi K3 (0.173) > Sonnet 5 (0.145) > Terra (0.135) > Luna (0.116) |
| Last checkpoint instead of best-of-3 | Opus 5 (0.240) > Sol (0.184) > Kimi K3 (0.159) > Sonnet 5 (0.142) > Terra (0.127) > Luna (0.110) |
| Max effort only (Kimi K3 ran only at max) | Sol (0.244) > Terra (0.228) > Opus 5 (0.222) > Kimi K3 (0.173) > Sonnet 5 (0.163) > Luna (0.138) |
| Each system's best configuration | Opus 5 (0.287) > Sol (0.244) > Terra (0.228) > Sonnet 5 (0.216) > Kimi K3 (0.173) > Luna (0.147) |
| Exclude effort "none" and "low" | Opus 5 (0.244) > Sol (0.204) > Kimi K3 (0.173) > Terra (0.159) > Sonnet 5 (0.156) > Luna (0.132) |
| Drop RAGEN (train/final board contamination) | Opus 5 (0.203) > Kimi K3 (0.180) > Sol (0.147) > Sonnet 5 (0.133) > Luna (0.126) > Terra (0.121) |
| RAGEN σ=1 cells (512/512) set to baseline | Opus 5 (0.195) > Kimi K3 (0.173) > Sol (0.160) > Sonnet 5 (0.145) > Terra (0.135) > Luna (0.116) |
| All confirmed corrections (NPO optimum 1.0; task-stated BTRM/OpenR1 baselines; DDPO degenerate cells capped at baseline; RAGEN dropped) | Opus 5 (0.257) > Kimi K3 (0.237) > Sol (0.208) > Sonnet 5 (0.181) > Luna (0.161) > Terra (0.161) |
| All confirmed corrections, max effort only | Opus 5 (0.252) > Kimi K3 (0.237) > Sol (0.219) > Sonnet 5 (0.210) > Terra (0.197) > Luna (0.186) |

## Run-to-run noise proxy

There is one run per cell. Differences between adjacent effort levels of the same model mix effort effects with run noise; non-monotone effort curves bound the noise from below.

- Opus 5: low 0.273, medium 0.287, high 0.277, xhigh 0.188, max 0.222
- Sol: none 0.125, low 0.197, medium 0.144, high 0.235, xhigh 0.193, max 0.244
- Sonnet 5: low 0.099, medium 0.109, high 0.216, xhigh 0.137, max 0.163
- Terra: none 0.065, low 0.108, medium 0.134, high 0.129, xhigh 0.144, max 0.228
- Luna: none 0.091, low 0.079, medium 0.124, high 0.119, xhigh 0.147, max 0.138

## Task bootstrap of the published system ranking (2000 replicates)

| System | #1 | #2 | #3 | #4 | #5 | #6 |
|---|---|---|---|---|---|---|
| Opus 5 | 98% | 2% | 0% | 0% | 0% | 0% |
| Sol | 0% | 59% | 37% | 3% | 1% | 0% |
| Kimi K3 | 2% | 39% | 47% | 6% | 6% | 0% |
| Sonnet 5 | 0% | 0% | 13% | 74% | 12% | 2% |
| Terra | 0% | 0% | 2% | 12% | 62% | 24% |
| Luna | 0% | 0% | 2% | 5% | 19% | 74% |

## Contribution of RAGEN to each system's mean σ

| System | Mean σ | Mean σ without RAGEN | RAGEN cells at σ = 1 |
|---|---|---|---|
| Opus 5 | 0.249 | 0.203 | 3 |
| Sol | 0.190 | 0.147 | 2 |
| Kimi K3 | 0.173 | 0.180 | 0 |
| Sonnet 5 | 0.145 | 0.133 | 0 |
| Terra | 0.135 | 0.121 | 0 |
| Luna | 0.116 | 0.126 | 0 |
