# FINAL CHECK — v1.5 Final Full Gate

## Final verdict
**ACTUAL TEST — PASS**

This is an executable synthetic-file Full Gate using newly generated PDF/MP4 submission packages after the v1.5 freeze.
It is NOT a third-party real-world submission corpus test.

Frozen validator SHA-256:
`4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11`

## Test integrity
- v1.5 policy and thresholds registered before holdout creation.
- v1.5 validator frozen before holdout creation.
- Final holdout created only after freeze.
- Fixture audit passed before scoring.
- Freeze hash rechecked before execution.
- No validator/policy changes after seeing final-holdout results.

## Test set
- Total: 39
- Clean: 12
- Critical BLOCKER mutations: 15
- R19 photo-only risk: 5
- Ambiguous Ken Burns: 4
- REVIEW-only: 3

## Hard Gate metrics
| Metric | Result | Gate |
|---|---:|---:|
| Critical Blocker Recall | 100.0% | >=90% |
| Deterministic Blocker Recall | 100.0% | >=98% |
| Text-PDF semantic Recall | 100.0% | >=95% |
| Scanned-PDF Vision Recall | 100.0% | >=90% |
| Clean scanned-PDF doc false block | 0.0% | <=5% |
| Evidence Coverage | 100.0% | 100% |
| R19 clear photo risk intercept | 100.0% | >=90% |
| R19 real-motion false BLOCKER | 0.0% | 0% |
| R19 ambiguous false BLOCKER | 0.0% | 0% |
| Bad/risky package -> READY | 0.0% | 0% |
| Clean package -> BLOCKED | 0.0% | <=5% |

## R19 policy
R19 is now REVIEW-only.

- PHOTO_ONLY -> REVIEW
- ambiguous/global pan-zoom -> REVIEW
- confident MOTION_VIDEO -> no R19 finding
- R19 automatic BLOCKER is forbidden

This fixed the unsafe behavior seen in v1.4.

### Important usability observation
Real-motion unnecessary R19 REVIEW rate was **83.3%**.

This was pre-registered as observational rather than a hard gate.
Therefore v1.5 is safe against false R19 BLOCKERs, but R19 remains noisy and should not be presented as a high-confidence automatic classifier in the MVP UI.

Recommended UI wording:
`REVIEW — 사진 기반 영상 여부를 직접 확인하세요.`

## Extractor status
The Requirement Extractor was not re-run in this Full Gate because it was unchanged.
The retained evidence is the prior actual independent-chat blind test:
- Recall: 100.0%
- Evidence coverage: 100.0%
- Unsupported blocker: 0
- Atomicity violations: 1

This prior test used a separate ChatGPT conversation for extraction, but its Gold was authored post-hoc in the evaluation conversation; it was not double-blind.

## Vision status
Scanned PDFs were actually rasterized and visually inspected.
The clean scan contained all required sections.
The mutation scan omitted the work-description section and was correctly converted to R11 BLOCKER.

Status:
**ACTUAL SAME-SESSION VISUAL TEST**
Not an independent vision-model blind evaluation.

## Product interpretation
Under the agreed pre-registered gates, the FINAL CHECK MVP validation structure PASSES:
- explicit rules -> deterministic checks
- semantic document checks -> text/vision path
- uncertain provenance/content rules -> REVIEW
- every finding -> announcement evidence
- no risky semantic rule is forced into an unsupported BLOCKER

The result supports moving from validation engineering to UI/demo implementation.

## Remaining limitations before production claims
1. Synthetic executable fixtures, not a large real-world user submission corpus.
2. R19 is safe but noisy: 83.3% of new real-motion fixtures received unnecessary REVIEW.
3. Vision fallback has not undergone an independent model blind test.
4. Extractor blind evidence is strong but not double-blind.
5. Production should keep REVIEW visible as uncertainty rather than marketing it as automatic detection.
