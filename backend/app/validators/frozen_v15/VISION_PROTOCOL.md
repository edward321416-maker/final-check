# FINAL CHECK v1.2 Vision Fallback Protocol

Use ONLY the rasterized PDF page images produced by validator_v1_2.py.
Do not use hidden case labels or filenames describing the mutation.

For each VISION_PENDING concept, visually determine whether the document section is clearly present:
- application: 참가 신청서
- privacy: 개인정보 수집/이용 동의서
- portrait: 초상권 사용 동의서
- description: 출품 영상작품 설명서

Decision:
- Clearly present -> PASS for that concept.
- Clearly absent -> BLOCKER for that concept.
- Ambiguous/unreadable -> REVIEW.

Do not infer presence from page count alone.
Do not use OCR or hidden ground truth.
