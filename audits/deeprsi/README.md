# DeepRSI audit

**Verdict: Flawed** (reviewed 2026-10-27; leaderboard of 2026-10-23, 15 tasks, 180 attempts).

- [`review.html`](review.html): the review in Epoch's Benchmark Review page format
- [`report.md`](report.md): the same review as Markdown, from `templates/audit-report.md`, with the sensitivity analysis and per-task verdicts
- [`task-log.csv`](task-log.csv): one row per task with classification and evidence
- [`setup.md`](setup.md): per-model harness, API and budget audit
- [`tasks/`](tasks): per-task notes
- [`data/trial_reviews/`](data/trial_reviews): per-attempt classification with evidence (180 attempts)
- [`data/adjudication.json`](data/adjudication.json): lead-auditor overrides of reviewer calls, with reasons
- [`data/summary.md`](data/summary.md), [`data/sensitivity.md`](data/sensitivity.md): generated tables
- [`REVIEW_PROTOCOL.md`](REVIEW_PROTOCOL.md): per-attempt review protocol
- [`scripts/`](scripts): fetch the public data, build the workspace, reproduce the Elo exactly, run the sensitivity analysis
