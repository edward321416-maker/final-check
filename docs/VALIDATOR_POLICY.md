# Validator policy — frozen Product Lock

The original Validator v1.5 Python implementation must remain authoritative.
TASK 01 contains fixture rendering and an explicitly unavailable adapter boundary.
It does not reimplement v1.5 and does not claim the frozen gate was rerun.

## Finding contract
- Exactly BLOCKER, REVIEW, PASS, EXTERNAL.
- BLOCKER requires nonblank announcement evidence and submission evidence, including source, locator and excerpt.
- R19 must never be an automatic BLOCKER, even if both evidence fields exist.
- PHOTO_ONLY suspicion, Ken Burns, pan, zoom and ambiguous motion require REVIEW.
- Confident real motion creates no R19 issue. A future complete evaluation may represent a checked no-issue condition as PASS; do not infer it merely from an absent result.
- Empty, incomplete, duplicate or unresolved findings never produce READY.
- EXTERNAL remains external. A file check cannot prove portal submission.

## Current execution
Mock results are loaded only for demo sessions and allowlisted fixture IDs.
Custom upload replaces all mock requirements/results/history and returns source_mode=unavailable.
No content extraction, semantic model, Vision call or real validator is running.
Uploads are streamed for bounded metadata/hash collection, then closed; this skeleton retains no durable upload content.

## Adapter sequence and next integration
The desktop/mobile golden path passed before v15_adapter.py was added.
ValidatorInput describes proposed application inputs, not the unknown native v1.5 signature.
The adapter currently always raises ValidatorUnavailable; the API returns 503.

Before wiring:
1. Supply the original versioned Python source, checksum/commit, native entrypoint, requirements and result schema.
2. Supply the frozen 39-package test assets and expected outputs without editing them.
3. Map native I/O inside the Python adapter; retain original engine code and algorithms.
4. Add local file-lifecycle handling and extraction based on approved retention/provider decisions.
5. Run contract checks, then the existing frozen regression gate. Report actual results separately from handoff claims.

## Demo fixture limits
The 10-second threshold, consent filename and synthetic announcement are demonstration data only.
R19=ambiguous is a mocked output independent of the generated test-pattern video.
The fixture's metadata agrees with its generated video duration, but the product UI does not measure video duration in TASK 01.
