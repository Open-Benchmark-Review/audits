# Open Benchmark Review: audits

The full evidence behind the reviews published at [openbenchmarkreview.org](https://openbenchmarkreview.org):
reports, task logs, per-task findings, review protocols and the scripts that reproduce every count.

Reviews apply [Epoch AI's benchmark review rubric](https://epoch.ai/data/benchmark-reviews-documentation/methodology)
(Rubric v1) as written, plus the documented extensions in [methodology/rubric.md](methodology/rubric.md).

## ML Benchmarks

| Benchmark | Version reviewed | Verdict | Reviewed | Report |
| --- | --- | --- | --- | --- |
| HackBench (Meta, RAM) | HF release v8, 169 records | **Flawed** | 2026-10-27 | [audits/hackbench](audits/hackbench/report.md) |
| FrontierCS 2 | 48 public tasks; leaderboard of 2026-10-26 | **Flawed** | 2026-10-27 | [audits/frontiercs-2](audits/frontiercs-2/report.md) |
| DeepRSI (Hillclimb) | 15 tasks, 180 attempts; leaderboard of 2026-10-23 | **Flawed** | 2026-10-27 | [audits/deeprsi](audits/deeprsi/report.md) |
| FrontierML (Induction Labs) | Repo `31837e0`; leaderboard of 2026-10-27 | **Flawed** | 2026-10-27 | [audits/frontierml](audits/frontierml/report.md) |
| AI4AI-Bench | 10 tasks, 29 configurations | **Flawed** | 2026-10-29 | [audits/ai4ai-bench](audits/ai4ai-bench/report.md) |

## What each audit folder holds

- `report.md`: the review, in the layout of Epoch AI's benchmark reviews
- `review.html`: the same review as a standalone page
- `task-log.csv`: one row per inspected task, with its classification and evidence
- `setup.md`: each leaderboard entry's model, harness and settings, where available
- `scripts/`: fetch the public data and reproduce every count
- `data/`, `tasks/`, `findings/`: per-task and per-attempt evidence

Some source datasets are gated or forbid rehosting. Those audits publish derived statistics and short quotes
only, with scripts that rebuild the rest from the original source.

## Methodology and templates

- [methodology/rubric.md](methodology/rubric.md): the rubric, verdict logic, thresholds, sampling and our extensions
- [templates/](templates/): the report, task log and setup checklist that every new audit starts from

## Corrections and responses

Open an issue with the review, the finding and your evidence, or email `reviews@openbenchmarkreview.org`.
Benchmark developers can ask for their response to be linked from the review.
