# Frozen v1.5 integration policy

## Immutable engine
backend/app/validators/frozen_v15/validator_v1_5.py is the original 15,851-byte source.
SHA-256: 4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11.
Git disables text conversion for frozen artifacts. Verify the hash before importing and before every worker run.
The module's validate_case(Path) is the native entrypoint. Do not patch its globals, rename files to hide violations, change thresholds or replace algorithms.
All adaptation lives in v15_adapter.py; the engine runs in a bounded child process using the backend Python runtime and UTF-8.
Dependency notices go to stderr; stdout carries unchanged raw JSON.

## Input and mapping
Only the exact pinned SOURCE_RULES requirement profile is supported.
CheckSession contains that profile plus actual upload receipts. Adapter verifies names, byte sizes and SHA-256 against stored files before executing.
Frozen BLOCKER maps to BLOCKER only with matching announcement quote and actual file evidence.
Frozen REVIEW maps to REVIEW. VISION_PENDING maps to REVIEW and incomplete.
Absent violations map to PASS only for an applicable completed check with supporting actual file/metadata/section evidence.
Text-section PASS verifies extracted section markers; it does not verify the truth or signatures of document contents.
Unknown fields/statuses, missing result envelope, bad hashes, execution errors and timeout cannot produce READY.
Protected R19 BLOCKER output is downgraded to REVIEW; R20/R21 always remain REVIEW/EXTERNAL.
Schema guards independently reject unsupported R19/R20/R21 automatic judgments.

## Output and summary
Raw JSON and UI-adapted results are separate artifacts.
Backend summary is BLOCKED if an evidence-backed blocker exists; otherwise REVIEW_REQUIRED if execution is incomplete or any REVIEW/EXTERNAL exists.
READY requires explicit completion, a complete unique result set, and only verified PASS results.
The current frozen profile necessarily keeps R20/R21 unresolved, so its normal fixed demo is REVIEW_REQUIRED.

## Vision and historical limits
No Vision model/provider is connected. Real scanned-PDF test returns four VISION_PENDING findings, mapped to R09/R10/R11 REVIEW with incomplete=true.
No blind Vision accuracy or historical 39-case gate reproduction is claimed.
Reference scorecard/report remain byte-for-byte handoff evidence under docs/reference_full_gate/.

## Actual artifacts
- artifacts/demo-fixture-audit.json: independent ffprobe/filesystem/pypdf audit before scoring.
- artifacts/v15-broken-raw.json and v15-fixed-raw.json: original engine output.
- artifacts/v15-broken-adapted.json and v15-fixed-adapted.json: UI result contract and submission summary.
- artifacts/source-integrity.json and v15-runtime-smoke.json: source and dependency evidence.
- artifacts/task01-baseline/: pre-integration baseline.
