# TASK 04 — frozen independent baseline

Eight actual announcements; Gold frozen before execution; unchanged local-rules-v1.
Manual, one-to-one scoring; PARTIAL receives no credit. Same agent authored Gold and scored.

| Metric | Actual result |
|---|---:|
| Gold / raw extracted | 173 / 211 |
| Recall | 32/173 = 18.50% |
| Precision | 32/211 = 15.17% |
| Modality accuracy on MATCH | 8/32 = 25.00% |
| Evidence exactness | 211/211 = 100.00% |
| Evidence semantic support | 51/211 = 24.17% |
| Atomicity violations | 18/211 = 8.53% |
| Hallucinated constraints | 0 |
| Unsupported BLOCKER / total BLOCKER | 0 / 0 |

| Case | Gold | Extracted | MATCH | Recall | Precision |
|---|---:|---:|---:|---:|---:|
| C01 | 49 | 89 | 8 | 16.33% | 8.99% |
| C02 | 14 | 14 | 4 | 28.57% | 28.57% |
| C03 | 6 | 5 | 2 | 33.33% | 40.00% |
| C04 | 44 | 26 | 10 | 22.73% | 38.46% |
| C05 | 2 | 3 | 0 | 0.00% | 0.00% |
| C06 | 7 | 10 | 1 | 14.29% | 10.00% |
| C07 | 19 | 20 | 3 | 15.79% | 15.00% |
| C08 | 32 | 44 | 4 | 12.50% | 9.09% |

65 Gold have only partial coverage; 76 have no candidate coverage.

Read [analysis and decision](analysis.md), [failure taxonomy](failure-taxonomy.md),
[manual pairs](../scoring/pairs.csv), [candidate audit](../scoring/candidates.tsv),
[source manifest](../manifest.json), and [Gold freeze](../gold_manifest.json).
Task completion and regression evidence are recorded in [RESULT_CODEX](../../../RESULT_CODEX.md).
