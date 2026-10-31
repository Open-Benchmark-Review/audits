# Re-scoring AI4AI-Bench from the published case pages

sigma from the paper's Table 2 anchors, applied to the checkpoint scores on each case page.

## Per-configuration mean sigma: best-of-3 (published rule) vs last checkpoint vs first checkpoint

| Model | Effort | Cells | Best of 3 | Last checkpoint | First checkpoint | Best − last |
|---|---|---|---|---|---|---|
| claude-opus-5 | medium | 10 | 0.287 | 0.279 | 0.270 | +0.008 |
| claude-opus-5 | high | 10 | 0.277 | 0.267 | 0.256 | +0.010 |
| claude-opus-5 | low | 10 | 0.273 | 0.264 | 0.252 | +0.009 |
| gpt-5.6-sol | max | 10 | 0.244 | 0.235 | 0.223 | +0.009 |
| gpt-5.6-sol | high | 10 | 0.235 | 0.233 | 0.224 | +0.002 |
| gpt-5.6-terra | max | 10 | 0.228 | 0.225 | 0.217 | +0.003 |
| claude-opus-5 | max | 10 | 0.222 | 0.216 | 0.206 | +0.006 |
| claude-sonnet-5 | high | 10 | 0.216 | 0.212 | 0.206 | +0.004 |
| gpt-5.6-sol | low | 10 | 0.197 | 0.191 | 0.183 | +0.006 |
| gpt-5.6-sol | xhigh | 10 | 0.193 | 0.188 | 0.185 | +0.005 |
| claude-opus-5 | xhigh | 10 | 0.188 | 0.173 | 0.174 | +0.016 |
| kimi-k3 | max | 10 | 0.173 | 0.159 | 0.168 | +0.015 |
| claude-sonnet-5 | max | 10 | 0.163 | 0.156 | 0.148 | +0.007 |
| gpt-5.6-luna | xhigh | 10 | 0.147 | 0.142 | 0.143 | +0.005 |
| gpt-5.6-terra | xhigh | 10 | 0.144 | 0.136 | 0.135 | +0.008 |
| gpt-5.6-sol | medium | 10 | 0.144 | 0.135 | 0.127 | +0.009 |
| gpt-5.6-luna | max | 10 | 0.138 | 0.135 | 0.132 | +0.003 |
| claude-sonnet-5 | xhigh | 10 | 0.137 | 0.136 | 0.127 | +0.001 |
| gpt-5.6-terra | medium | 10 | 0.134 | 0.127 | 0.127 | +0.006 |
| gpt-5.6-terra | high | 10 | 0.129 | 0.120 | 0.125 | +0.009 |
| gpt-5.6-sol | none | 10 | 0.125 | 0.122 | 0.119 | +0.003 |
| gpt-5.6-luna | medium | 10 | 0.124 | 0.113 | 0.121 | +0.011 |
| gpt-5.6-luna | high | 10 | 0.119 | 0.109 | 0.118 | +0.010 |
| claude-sonnet-5 | medium | 10 | 0.109 | 0.108 | 0.107 | +0.001 |
| gpt-5.6-terra | low | 10 | 0.108 | 0.106 | 0.106 | +0.003 |
| claude-sonnet-5 | low | 10 | 0.099 | 0.096 | 0.095 | +0.004 |
| gpt-5.6-luna | none | 10 | 0.091 | 0.091 | 0.088 | +0.000 |
| gpt-5.6-luna | low | 10 | 0.079 | 0.069 | 0.071 | +0.009 |
| gpt-5.6-terra | none | 10 | 0.065 | 0.048 | 0.062 | +0.017 |

All 290 cells: best-of-3 0.165, last checkpoint 0.158.
Cells below the baseline (sigma < 0.1) under best-of-3: 126; under last checkpoint: 147.
Cells whose beat/miss-the-baseline outcome flips between best-of-3 and last checkpoint: 21.

Cells at sigma = 1 (the declared task optimum): claude__ragen_sokoban_grpo__claude-opus-5__high (1.0), claude__ragen_sokoban_grpo__claude-opus-5__low (1.0), claude__ragen_sokoban_grpo__claude-opus-5__medium (1.0), codex__ragen_sokoban_grpo__gpt-5.6-sol__high (1.0), codex__ragen_sokoban_grpo__gpt-5.6-sol__max (1.0)

## Per-system mean (all efforts)

| System | Cells | Best of 3 | Last checkpoint |
|---|---|---|---|
| claude-opus-5 | 50 | 0.249 | 0.240 |
| gpt-5.6-sol | 60 | 0.190 | 0.184 |
| kimi-k3 | 10 | 0.173 | 0.159 |
| claude-sonnet-5 | 50 | 0.145 | 0.142 |
| gpt-5.6-terra | 60 | 0.135 | 0.127 |
| gpt-5.6-luna | 60 | 0.116 | 0.110 |

## Per-task mean sigma

| Task | Best of 3 | Last checkpoint | Cells at 0 | Cells < 0.1 |
|---|---|---|---|---|
| DDPO | 0.171 | 0.167 | 1 | 12 |
| DiGress | 0.089 | 0.087 | 4 | 17 |
| DPO | 0.187 | 0.173 | 0 | 7 |
| Soup | 0.120 | 0.118 | 1 | 1 |
| OPD | 0.086 | 0.084 | 4 | 24 |
| OpenR1 | 0.091 | 0.088 | 1 | 25 |
| NPO | 0.146 | 0.140 | 1 | 5 |
| OWL | 0.325 | 0.324 | 1 | 2 |
| RAGEN | 0.338 | 0.315 | 7 | 12 |
| BTRM | 0.097 | 0.088 | 1 | 21 |
