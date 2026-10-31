# FrontierML audit

**Verdict: Flawed** (reviewed 2026-10-27; repo `31837e0`, 21 tasks × 3 wallets; 378 trials of six models audited
in full, 1,197 trials of 19 models used for leaderboard-wide statistics).

- [`review.html`](review.html): the review in Epoch's Benchmark Review page format
- [`report.md`](report.md): the same review as Markdown, from `templates/audit-report.md`
- [`findings.md`](findings.md): the full write-up, covering test-set integrity, task design, memory vs. skill, and
  questions for Induction Labs
- [`task-log.csv`](task-log.csv): one row per task with rubric code and evidence, plus a benchmark-wide row
- [`setup.md`](setup.md): per-model harness, API and budget audit
- [`tasks/`](tasks): per-task notes
- [`data/trial_reviews/`](data/trial_reviews): per-trial classification with evidence
- [`data/task_design/`](data/task_design): per-task design review with `path:line` citations
- [`data/adjudication.json`](data/adjudication.json): lead-auditor overrides, and the mapping of task-design findings
  onto the rubric
- [`data/summary.md`](data/summary.md), [`data/sensitivity.md`](data/sensitivity.md),
  [`data/source_origin.json`](data/source_origin.json): generated tables
- [`REVIEW_PROTOCOL.md`](REVIEW_PROTOCOL.md): per-trial review protocol
- [`scripts/`](scripts): fetch the public data, build the workspace, reproduce the leaderboard, run the sensitivity
  analysis
