# AI4AI-Bench audit

**Verdict: Flawed** (reviewed 2026-10-29; arXiv 2608.20318 v1, repo `5ced1e2`, 10 tasks × 29 configurations =
290 cells).

- [`review.html`](review.html): the review in Epoch's Benchmark Review page format
- [`report.md`](report.md): the same review as Markdown, from `templates/audit-report.md`
- [`task-log.csv`](task-log.csv): one row per task with rubric code and `path:line` evidence, plus a
  benchmark-wide row
- [`setup.md`](setup.md): per-system harness, effort, budget and failure audit
- [`tasks/`](tasks): per-task notes
- [`data/task_reviews/`](data/task_reviews): task-level findings and per-cell classification (290 cells)
- [`data/adjudication.json`](data/adjudication.json): lead-auditor overrides and the verified evidence for each
  counted defect
- [`data/cases.csv`](data/cases.csv), [`data/cells.json`](data/cells.json): parsed case pages and recomputed σ
- [`data/rescoring.md`](data/rescoring.md), [`data/ranking.md`](data/ranking.md), [`data/summary.md`](data/summary.md):
  generated tables
- [`REVIEW_PROTOCOL.md`](REVIEW_PROTOCOL.md): review protocol
- [`scripts/`](scripts): fetch the repo and case pages, parse, rescore and re-rank
