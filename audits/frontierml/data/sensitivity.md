# FrontierML ranking sensitivity (six audited models)

Cells are rank among the six (score, change from published). Scores are means over 21 tasks, 0-100.

## 1. Published

| Wallet | Opus | Astra | Fable | Argon | DeepSeek | Muse |
|---|---|---|---|---|---|---|
| $10 | 1 (45.4) | 2 (37.6) | 3 (35.7) | 4 (29.6) | 6 (21.3) | 5 (21.6) |
| $50 | 1 (52.4) | 2 (42.8) | 3 (37.4) | 4 (30.4) | 5 (22.5) | 6 (17.2) |
| $200 | 1 (58.8) | 2 (44.5) | 3 (41.9) | 4 (39.5) | 5 (23.5) | 6 (19.3) |

Pooled over the three wallets (63 runs per model): Opus 52.2 > Astra 41.6 > Fable 38.4 > Argon 33.2 > DeepSeek 22.4 > Muse 19.4

## 2. Leave one task out ($200)

20 of 21 variants leave the $200 order unchanged.

| Task dropped | Opus | Astra | Fable | Argon | DeepSeek | Muse |
|---|---|---|---|---|---|---|
| llm-post-train | 1 (58.4, -0.4) | 3 (43.4, -1.1) | 2 (44.0, +2.1) | 4 (38.6, -0.9) | 5 (23.9, +0.4) | 6 (17.8, -1.5) |

## 3. Bootstrap over tasks (10,000 replicates)

**$10**: share of replicates at each rank

| Model | 1st | 2nd | 3rd | 4th | 5th | 6th |
|---|---|---|---|---|---|---|
| Opus | 100% | 0% | 0% | 0% | 0% | 0% |
| Astra | 0% | 73% | 26% | 1% | 0% | 0% |
| Fable | 0% | 27% | 71% | 3% | 0% | 0% |
| Argon | 0% | 0% | 3% | 91% | 5% | 1% |
| DeepSeek | 0% | 0% | 0% | 5% | 45% | 50% |
| Muse | 0% | 0% | 0% | 1% | 50% | 49% |

**$50**: share of replicates at each rank

| Model | 1st | 2nd | 3rd | 4th | 5th | 6th |
|---|---|---|---|---|---|---|
| Opus | 100% | 0% | 0% | 0% | 0% | 0% |
| Astra | 0% | 80% | 20% | 0% | 0% | 0% |
| Fable | 0% | 20% | 64% | 14% | 2% | 0% |
| Argon | 0% | 0% | 15% | 79% | 5% | 0% |
| DeepSeek | 0% | 0% | 0% | 7% | 83% | 10% |
| Muse | 0% | 0% | 0% | 0% | 10% | 90% |

**$200**: share of replicates at each rank

| Model | 1st | 2nd | 3rd | 4th | 5th | 6th |
|---|---|---|---|---|---|---|
| Opus | 100% | 0% | 0% | 0% | 0% | 0% |
| Astra | 0% | 63% | 26% | 11% | 0% | 0% |
| Fable | 0% | 26% | 49% | 25% | 0% | 0% |
| Argon | 0% | 11% | 25% | 64% | 0% | 0% |
| DeepSeek | 0% | 0% | 0% | 0% | 90% | 9% |
| Muse | 0% | 0% | 0% | 0% | 9% | 91% |

**pooled**: share of replicates at each rank

| Model | 1st | 2nd | 3rd | 4th | 5th | 6th |
|---|---|---|---|---|---|---|
| Opus | 100% | 0% | 0% | 0% | 0% | 0% |
| Astra | 0% | 82% | 17% | 1% | 0% | 0% |
| Fable | 0% | 17% | 80% | 3% | 0% | 0% |
| Argon | 0% | 0% | 3% | 96% | 0% | 0% |
| DeepSeek | 0% | 0% | 0% | 0% | 90% | 10% |
| Muse | 0% | 0% | 0% | 0% | 10% | 90% |

## 4. Run-to-run noise

11 (model, task) pairs spent under $10 at both the $50 and $200 wallets, so the extra budget went unused. Their two runs differ by a median of 5.2 points (mean 11.7, max 42.3); 2 differ by 20+ points.

| Model | Task | $50 score | $200 score |
|---|---|---|---|
| DeepSeek | end-of-turn | 42.3 | 0.0 |
| Muse | pii-redaction | 39.3 | 63.4 |
| Argon | screenshot-generation | 18.9 | 0.0 |
| Argon | screen-difference | 7.1 | 22.3 |
| DeepSeek | lean-simplification | 27.1 | 14.7 |
| Muse | end-of-turn | 5.2 | 0.0 |
| DeepSeek | idm-training | 39.5 | 43.3 |
| Argon | pokemon-random-battle | 0.0 | 3.6 |
| Argon | lean-simplification | 23.0 | 25.5 |
| DeepSeek | screenshot-generation | 38.6 | 37.6 |

Wallet steps ($10 to $50, $50 to $200) where the larger wallet scored 5+ points lower, of 42 per model: Opus 6, Astra 5, Fable 8, Argon 10, DeepSeek 12, Muse 13.

Gaps between adjacent models at $200: Argon > DeepSeek by 16.1, Opus > Astra by 14.3, DeepSeek > Muse by 4.2, Astra > Fable by 2.6, Fable > Argon by 2.4.

## 5. Reviewer outcomes, all 19 models

| Model | pass | fail | skipped | none / incomplete |
|---|---|---|---|---|
| claude-haiku-5-5 | 63 | 0 | 0 | 0 |
| claude-opus-5-5 | 63 | 0 | 0 | 0 |
| gpt-6-1-sol | 63 | 0 | 0 | 0 |
| gpt-6-luna | 63 | 0 | 0 | 0 |
| kimi-k3-1-pro | 63 | 0 | 0 | 0 |
| claude-sonnet-5-5 | 62 | 1 | 0 | 0 |
| gpt-6-astra | 62 | 1 | 0 | 0 |
| deepseek-v4-1-flash | 40 | 2 | 21 | 0 |
| minimax-m3-1-flash | 44 | 2 | 17 | 0 |
| gemini-4-argon | 60 | 3 | 0 | 0 |
| muse-spark-1-3 | 58 | 3 | 0 | 2 |
| muse-wonder | 60 | 3 | 0 | 0 |
| claude-fable-5-1 | 59 | 4 | 0 | 0 |
| gemini-3-8-flash | 58 | 4 | 0 | 1 |
| glm-5-3 | 55 | 6 | 1 | 1 |
| kimi-k3 | 57 | 6 | 0 | 0 |
| grok-4-7 | 55 | 7 | 0 | 1 |
| qwen3-8-max | 55 | 8 | 0 | 0 |
| beam-1-0 | 49 | 10 | 1 | 3 |

Claude models: 5 fails of 252 reviewed (2.0%); other models: 55 of 897 (6.1%). One-sided Fisher exact p (non-Claude fail rate higher) = 0.0040. A lower fail rate can also mean cleaner runs; section 6 and the per-task reviews test which.

## 5b. Does money help, task by task?

FrontierML claims agents turn capital into performance. Per task: mean score of all 19 models at $10 and $200, and for the six strongest by published $200 score, the mean change, how many improved, and their mean $200 wallet spend.

| Task | All 19 at $10 | All 19 at $200 | Change | Top-6 change | Top 6 improved | Top-6 $200 spend |
|---|---|---|---|---|---|---|
| llm-diffusion | 2.0 | 17.1 | +15.0 | +38.8 | 5/6 | $164 |
| babylm-replay | 30.4 | 38.2 | +7.7 | +25.5 | 5/6 | $71 |
| speculative-drafting | 6.0 | 14.1 | +8.1 | +15.4 | 6/6 | $139 |
| ternary-ptq | 4.8 | 10.7 | +5.9 | +15.0 | 6/6 | $130 |
| ocr-latent-compression | 19.9 | 22.8 | +2.9 | +14.3 | 4/6 | $121 |
| llm-post-train | 18.6 | 27.6 | +9.0 | +13.1 | 4/6 | $169 |
| music-transcription | 15.4 | 20.9 | +5.5 | +12.9 | 5/6 | $97 |
| svg-generation | 0.7 | 4.1 | +3.4 | +10.1 | 4/6 | $184 |
| idm-training | 41.1 | 43.0 | +1.9 | +10.0 | 5/6 | $84 |
| ai-text-detection | 69.7 | 73.0 | +3.3 | +9.3 | 4/6 | $63 |
| lean-validity | 17.4 | 22.7 | +5.3 | +9.1 | 4/6 | $112 |
| screen-difference | 13.4 | 14.2 | +0.8 | +5.8 | 5/6 | $85 |
| scitikz | 45.2 | 48.4 | +3.2 | +5.4 | 6/6 | $145 |
| lean-simplification | 15.8 | 14.6 | -1.2 | +1.9 | 5/6 | $18 |
| maple-vlm | 0.0 | 0.1 | +0.1 | +0.3 | 1/6 | $100 |
| screenshot-generation | 29.7 | 32.4 | +2.7 | +0.2 | 4/6 | $30 |
| pokemon-random-battle | 0.6 | 0.6 | +0.0 | +0.2 | 3/6 | $64 |
| pii-redaction | 49.7 | 52.6 | +2.8 | -0.4 | 2/6 | $72 |
| end-of-turn | 37.0 | 24.2 | -12.8 | -1.2 | 3/6 | $22 |
| video-frame-interpolation | 45.4 | 50.7 | +5.3 | -4.8 | 1/6 | $100 |
| zero-shot-classification | 35.5 | 33.3 | -2.2 | -11.4 | 2/6 | $40 |

Top six: Opus, claude-sonnet-5-5, Astra, Fable, Argon, gpt-6-1-sol. 8 of 21 tasks show a top-6 gain of 2 points or less from $10 to $200: end-of-turn, lean-simplification, maple-vlm, pii-redaction, pokemon-random-battle, screenshot-generation, video-frame-interpolation, zero-shot-classification.

## 6. Audit corrections

| Scenario | Wallet | Opus | Astra | Fable | Argon | DeepSeek | Muse |
|---|---|---|---|---|---|---|---|
| Published | $10 | 1 (45.4) | 2 (37.6) | 3 (35.7) | 4 (29.6) | 6 (21.3) | 5 (21.6) |
| Published | $50 | 1 (52.4) | 2 (42.8) | 3 (37.4) | 4 (30.4) | 5 (22.5) | 6 (17.2) |
| Published | $200 | 1 (58.8) | 2 (44.5) | 3 (41.9) | 4 (39.5) | 5 (23.5) | 6 (19.3) |
| Zero the 5 confirmed false positives | $10 | 1 (45.4) | 2 (37.6) | 3 (35.4, -0.4) | 4 (29.1, -0.5) | 6 (21.3) | 5 (21.6) |
| Zero the 5 confirmed false positives | $50 | 1 (52.4) | 2 (42.8) | 3 (33.8, -3.6) | 4 (30.4) | 5 (22.5) | 6 (17.2) |
| Zero the 5 confirmed false positives | $200 | 1 (58.8) | 2 (44.5) | 3 (40.5, -1.4) | 4 (39.5) | 5 (23.5) | 6 (19.3) |
| Zero every trial a task reviewer called a false positive, before adjudication (11) | $10 | 1 (45.4) | 2 (37.6) | 3 (35.4, -0.4) | 4 (29.1, -0.5) | 6 (20.3, -1.0) | 5 (21.6) |
| Zero every trial a task reviewer called a false positive, before adjudication (11) | $50 | 1 (52.4) | 2 (42.8) | 3 (33.8, -3.6) | 4 (30.4) | 5 (20.5, -2.0) | 6 (17.2) |
| Zero every trial a task reviewer called a false positive, before adjudication (11) | $200 | 1 (58.8) | 2 (44.5) | 3 (40.5, -1.4) | 4 (32.3, -7.2) | 5 (23.2, -0.3) | 6 (19.3) |
| Strict reading: confirmed plus probable false positives and the contested llm-diffusion winner (11) | $10 | 1 (45.4) | 2 (37.6) | 3 (35.4, -0.4) | 4 (29.1, -0.5) | 6 (20.3, -1.0) | 5 (21.6) |
| Strict reading: confirmed plus probable false positives and the contested llm-diffusion winner (11) | $50 | 1 (52.4) | 2 (42.8) | 3 (33.8, -3.6) | 4 (30.4) | 5 (20.5, -2.0) | 6 (17.2) |
| Strict reading: confirmed plus probable false positives and the contested llm-diffusion winner (11) | $200 | 1 (58.8) | 2 (44.5) | 3 (40.5, -1.4) | 4 (32.3, -7.2) | 5 (23.2, -0.3) | 6 (19.3) |
| Zero every reward hack (13) | $10 | 1 (45.4) | 2 (37.6) | 3 (35.4, -0.4) | 4 (29.1, -0.5) | 6 (21.3) | 5 (21.6) |
| Zero every reward hack (13) | $50 | 1 (52.4) | 2 (42.8) | 3 (33.8, -3.6) | 4 (30.4) | 5 (22.5) | 6 (17.2) |
| Zero every reward hack (13) | $200 | 1 (58.8) | 2 (44.5) | 3 (40.5, -1.4) | 4 (39.5) | 5 (23.5) | 6 (19.3) |

1 trials were judged false negatives (zeroed but legitimate): 61zfoj. Their pre-review metric is not published, so they cannot be restored here.
