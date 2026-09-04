# Failure taxonomy

Counts come from saved manual tables, not a generated classifier. A candidate can
carry multiple labels. Gold-side counts here cover only the 76 requirements with
no candidate coverage; the 65 partially covered Gold are represented in pairs.csv.
Do not add the columns to estimate a requirement-level failure rate.

| Category | Candidate annotations | Wholly uncovered Gold | Meaning |
|---|---:|---:|---|
| FALSE_POSITIVE | 58 | 0 | Non-obligations extracted |
| MISS_KEYWORD | 0 | 43 | Actual rule omitted by subject selection |
| WRONG_MODALITY | 37 | 0 | Obligation strength/permission incorrect |
| EVIDENCE_NOT_SUPPORTING | 35 | 0 | Quote fragment/heading does not establish rule |
| TABLE_FAILURE | 23 | 11 | Row/column or field relationships lost |
| MISS_CONDITION | 21 | 12 | Applicant, stage, exception or context lost |
| PDF_READING_ORDER | 19 | 1 | PDF text fragments break meaning |
| ATOMICITY | 18 | 0 | Multiple independent constraints in one candidate |
| DUPLICATE | 7 | 0 | No second match credit for a restatement |
| MISS_IMPLICIT_RULE | 1 | 9 | Duty is implicit rather than explicit command |
| OTHER | 3 | 0 | Source deadline conflict or frozen Gold scope limitation |
| WRONG_VERIFIER | 1 | 0 | Observed eligibility routing error; no global verifier accuracy claim |

No standalone NEGATION_FAILURE count is asserted: the observed negation examples
are counted under lost conditions, compound modality or table evidence. The exact
unobserved negation phrase remains NOT TESTED. Hallucinations and unsupported
BLOCKER are zero under PROTOCOL.md's separate definitions.

Semantic support is a per-candidate binary judgment in candidates.tsv. Its 160
unsupported candidates need not equal the 35 EVIDENCE_NOT_SUPPORTING labels:
false positives, condition loss, table fragments and wrong modality can also fail
semantic support. Modality accuracy uses only the 32 full MATCH pairs, whereas the
37 WRONG_MODALITY annotations also include partials and duplicates.
