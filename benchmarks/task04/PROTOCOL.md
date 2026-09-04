# TASK 04 protocol — written before baseline execution

Baseline: main `81bf2551c5967836d3e54869de2e86261428c78e`, unchanged
`local-rules-v1`. Eight distinct real competitions, selected for source availability
and organization/document diversity, not extractor performance. No synthetic cases
enter this corpus. Historical prerequisite failure is excluded.

## Order and source scope

1. Save original public HTML/PDF bytes, URLs, retrieval timestamps and hashes.
2. Save announcement body text. HTML navigation/duplicate responsive copies may be
   removed with documented boundaries; no rewriting or sentence repair. PDF text
   uses the application's PDF reader and page order. Preserve table fragmentation.
3. Read source documents and author atomic applicant-facing Gold, including
   conditional duties, permissions and recommendations. Deduplicate restatements.
   Exclude promotion, prizes, organizer operations and non-obligation schedules.
   Empty form field labels alone are not obligations; explicit form instructions,
   signature and consent requirements are. Each case records document scope;
   linked documents outside that scope are not silently treated as read.
4. Save Gold SHA-256 manifest with UTC timestamp and commit it BEFORE importing
   or invoking the baseline extractor. Regression tests also wait until freeze.
5. Execute baseline once, retain raw candidates and actual evidence-gate output.
6. Manually score, aggregate, run existing regression and report without tuning.

## Frozen scoring definitions

Primary denominator is all raw LocalRuleExtractor candidates, including rejected
ones. Gate acceptance and review flags are reported separately. Every Gold and
every candidate must have a scoring row. MATCH is one-to-one semantic equivalence
of a complete atomic obligation (including its condition/exception). Modality
errors are measured separately and do not erase an otherwise complete content
match. A compound candidate receives PARTIAL for covered Gold, never multiple
full matches. Duplicates get no second credit. PARTIAL scores zero, not half.

- Recall: distinct fully matched Gold / all Gold.
- Precision: distinct fully matched candidates / all raw candidates.
- Modality accuracy: correct modality / MATCH pairs; N/A for zero matches.
- Exactness: nonempty evidence quote is a literal input substring / candidates.
- Semantic support: quote/context supplied in the candidate is sufficient for its
  asserted applicant rule, condition and modality / candidates. Merely copying
  promotional text, an incomplete fragment or a heading is insufficient. A
  complete supported INFO restatement can be supported despite wrong modality;
  a weakened/strengthened permission/prohibition is unsupported.
- Atomicity: candidates combining independently checkable constraints / candidates.
- Hallucinated rule: invented constraint absent from the complete scoped source;
  headings/promotion are false positives, not invented constraints. An unsupported
  assertion of permission/prohibition counts when it contradicts the source.
- Unsupported BLOCKER: BLOCKER candidates lacking supporting source evidence.

Failure categories may overlap. Gold-side absence and candidate-side defects are
counted separately to avoid confusing missed obligations with bad output volume.
Record repeated-quote first-occurrence anchoring; do not repair it. Inspect real
negation if present; do not fabricate a case solely to fill a taxonomy category.

## Independence and limits

INDEPENDENT means real third-party announcements and Gold frozen before their
outputs, as defined by TASK 04. The same engineering agent authors Gold and scores;
it has inspected the implementation. This is not an implementation-blind or
independently human-adjudicated study. No model/provider comparison is performed.
Eight purposively selected cases are a decision aid, not a population estimate.
Only executed code/files are ACTUAL TEST. Existing synthetic regression is SELF
or SIMULATED where applicable, and is never pooled into primary metrics.

No product/extractor/frozen-validator modifications; no post-analysis tuning;
no TASK 05 implementation; PR remains open for Product/Business Lead review.
