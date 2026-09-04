# TASK 04 interpretation and engineering recommendation

TASK 04 **PASS**: this was a measurement task, not an extractor score gate.
FINAL CHECK **GO** remains locked. Recommend **AI-FIRST + DETERMINISTIC EVIDENCE
GATE** as the next candidate for Product/Business Lead review. Replace local rules
as the primary extraction strategy; the present implementation is unchanged.
No AI model was evaluated, so this is a proposed experiment, not proof that AI will
perform better. No TASK 05 implementation or provider selection has started.

## What was actually measured

The frozen 173 Gold requirements yielded 211 raw candidates. All 211 passed the
existing schema/exact-quote gate. Only 32 fully matched atomic Gold, under the
pre-output one-to-one policy. There are 65 partially covered Gold and 76 with no
candidate coverage. Partial items receive zero credit; duplicates receive no
second credit. Modality is scored separately from complete content matches.

Results: recall **18.50%**, precision **15.17%**, modality **25.00%** (8/32),
exact quotes **100%** (211/211), semantic support **24.17%** (51/211), atomicity
violations **18 / 211 (8.53%)**, invented constraints **0**, unsupported BLOCKER
**0** (total BLOCKER is also zero). These are manual judgments on this sample,
not population accuracy or calibrated confidence. See [generated metrics](report.md).

Three largest practical failure groups, with explicit counting units:

1. FALSE_POSITIVE: 58 output candidates are titles, organizer activity, award
   entries or other non-requirements. C06 has award-table organization names in
   the accepted requirement list.
2. MISS_KEYWORD: 43 wholly uncovered Gold duties/permissions. C04 misses model
   cutoff/license conditions, API/data restrictions, offline inference, code
   details and leakage restrictions. C03 misses the actual Google Forms route.
3. WRONG_MODALITY: 37 candidate annotations (including partial/duplicate items);
   among full MATCH only, 24/32 have the wrong modality. Ability to prove or
   reproduce something is repeatedly treated as optional MAY.

Failures are broad rather than a narrow missing-pattern list. Repeated regex
tuning against these eight announcements is not recommended. Existing full-source
human review must remain mandatory while a separately authorized AI-first path
is evaluated; exact evidence gating is necessary but insufficient.

## Required failure probes

- Implicit obligation: C04 team cap, report filename list and Python language;
  C01 consent obligations expressed through refusal preventing participation.
- Conditions: C01 per-person/under-14/actor consent and C08 track-specific forms
  lose context. C04 model-file fragments lose the finalist condition.
- Negation: real C04 individual submission without team registration is correctly
  preserved as MAY. C07 receipt-number "leave blank" is lost; C02 private-account
  prohibition is bundled with positive submission obligations under MUST_NOT.
  The exact phrase `제출하지 않아도 된다` is absent; that specific phrase is
  **NOT TESTED**. No synthetic negation case was added to fill a category.
- SHOULD vs MUST: C01 PDF/MP4 recommendations are table-dependent. C02 resolution,
  format and orientation remain one compound item; C01 video-file recommendation
  is correctly preserved. Recommended resolution is entirely missed in C01.
- Compound rules: 18 manually identified output violations. Only 1/18 has the
  existing NEEDS_REVIEW atomicity flag; no detector code was changed. C06-G001
  combines nationality, team participation and size despite profile state DRAFT.
  DRAFT is not CONFIRMED and is not a submission PASS/READY verdict.
- Tables and PDF order: C01 filenames/form relationships and C08 conditional
  document table are fragmented. C05 visually readable dates are separated into
  many text fragments. Period-based sentence splitting also damages C01/C07/C08
  numeric dates; this is not solely a PDF-layout problem.
- Repeated quote: 35 actual anchors point to the first substring occurrence rather
  than the candidate's declared source line (C01 27, C05 1, C06 4, C07 1, C08 2).
  C01-G012's filename heading declares line39 but anchors to the earlier heading.
  Repeated signature labels lose signer/form context. Exactness remains 100%.
  See [actual gate/anchor audit](gate-and-anchor-audit.json). No anchor fix applied.

## Independence, annotation limitations and score interpretation

These are actual third-party announcements, not synthetic examples written to
match the extractor. Gold was written before their outputs, frozen at
2026-09-03T11:46:35.794398+00:00, and committed as `5d4bb99` before execution.
Commit `978b911` additionally preserved original HTML bytes against Git newline
conversion before execution. The Gold files and their hashes did not change.
Runner audit verifies both current bytes and the Git freeze commit bytes.

The engineering agent had seen the implementation and performed both annotation
and manual scoring. **No independent human adjudicator and no implementation-blind
review.** C05 is a short one-page official PDF with two requirements; case sizes
vary substantially. Four HTML bodies use documented whitespace/block extraction;
this is the product's pasted-text path, not a shipped URL fetcher. Other tabs and
linked forms excluded by each source scope remain unread. No sampled case was
removed after seeing output, and no threshold or confidence interval is inferred.

Post-output annotation limitations are retained rather than silently fixing Gold:
C04-G022 provides a valid route for other inquiries omitted from frozen Gold;
C08-G040 is supported clerical-error liability information outside its Gold duty
list. These receive semantic support but no full-match precision credit. C04-G020
also includes a historical unfair-submission evaluation restriction not separately
annotated in Gold. Full candidate reviews and reasons are saved. A separate human
review may disagree about these boundaries, signatures or modality; the published
primary score remains the frozen-policy score, without post-hoc Gold correction.

Zero hallucinated constraints means no invented new condition was identified in
the verbatim outputs. Wrong scope/modality, incomplete fragments and false positives
are counted separately; zero does not imply safe or useful extraction. Zero
unsupported BLOCKER reflects this provider emitting no BLOCKER candidates, not
proof of recall or successful submission validation.

## Actual execution and limits

The initial post-freeze capture wrapper failed to serialize Pydantic requirements.
All eight failed saves are preserved in `extracted/*.json`; no candidate text or
score was available from that attempt. Only the capture wrapper was corrected to
use model_dump. The valid unchanged-baseline run is in `extracted/baseline/`.
This harness failure and the earlier prerequisite non-start are excluded from
benchmark scores. Subsequent runner invocations reuse hash-verified saved outputs;
they do not rerun or tune the extractor.

Regression: backend **47 passed**, browser **14 passed** (desktop/mobile Chromium),
TypeScript **PASS**, production build **PASS**. The backend has one existing
Starlette/httpx deprecation warning. Browser tooling reports color-environment
warnings. No test or product source was changed. Prior TASK03 generated artifacts
were restored after copying this run's outputs to `artifacts/task04/`.

Frozen v1.5 SHA before/after:
`4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11`.
Extractor/profile source hashes also match. Backend, frontend, fixtures, product
spec and validator policy have no diff from the TASK03 baseline.

- INDEPENDENT BENCHMARK: eight actual announcement snapshots, 173 pre-output Gold,
  actual local-rules execution and saved manual scoring.
- ACTUAL TEST: source ingestion, local extractor/gate, hash/anchor audit, existing
  backend and real-browser regression, typecheck/build. Actual is not synonymous
  with independent or expert-validated.
- SELF-BENCHMARK: existing generated demo/text/PDF fixtures used by regression;
  excluded from primary scores. No new synthetic benchmark cases.
- SIMULATED: existing injected providers and backend-failure regression behavior;
  excluded from primary scores. No external AI judge.
- NOT TESTED: external LLM/AI comparison, Vision/OCR, mixed image/text semantic
  extraction, generic automatic verification, historical 39-case reproduction,
  production hosting, exact unobserved negation phrase, independent human Gold
  review, private-company-only announcement coverage, other browser engines.

Next candidate: a bounded AI-first requirement extractor comparison retaining
deterministic quote checks and explicit human review. Product/Business Lead must
review TASK04 and decide scope/provider first. The delivery PR remains open.
