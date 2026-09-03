# TASK 02 real validator demo
These are synthetic submission files processed by the real frozen engine; findings are not canned.

1. Open http://127.0.0.1:3100. Click "demo 검사 시작하기".
2. Announcement Analysis shows 16 fixed requirements from the supplied frozen SOURCE_RULES. This is a handoff excerpt, not fresh AI extraction.
3. On Submission Upload click "문제 있는 demo 불러오기". The browser downloads the actual 61-second MP4 and PDF, then uploads their bytes to FastAPI.
4. Click "Preflight 실행하기". The original frozen Python validate_case runs in a child process.
5. Results: BLOCKED. R09 privacy consent and R13 duration are BLOCKER with both evidence sources. R19/R20/R21 are REVIEW.
6. Filter BLOCKER and inspect the extracted PDF section text and measured 61-second duration.
7. Click "수정 후 재검사", then "수정한 demo 불러오기". The replacement files are actually uploaded: privacy section restored and 45-second MP4.
8. Click "재검사 실행하기". A new frozen run clears R09/R13 blockers. Two changes are shown. Summary remains REVIEW_REQUIRED because R19/R20/R21 require review.
9. Reload the page: the session persists while its local backend process and one-hour TTL remain active.

You can also choose local PDF/MP4 files under the selected fixed profile. The expected team/file names remain 테스트어린이집_숏폼공모서류.pdf and 테스트어린이집_숏폼영상.MP4.
Custom announcement input now uses the separate TASK 03 generic review flow below. It never inherits frozen rules.
Image-only PDFs are rendered by the frozen engine but stay REVIEW without a Vision provider.

## TASK 03 generic profile demo
1. Home: paste fixtures/announcements/submission.txt into "공고문 텍스트", then choose "텍스트 공고로 시작". Alternatively upload submission.pdf from that directory.
2. Announcement Analysis: choose "요구사항 추출 실행". The visible provider is ACTUAL local rules, no AI model. Five synthetic example candidates appear; all need review.
3. Inspect exact evidence, offsets and source hashes. Edit G001 and save; it becomes NEEDS_REVIEW. Optionally delete the suggested video item G004. The original candidate and deletion remain in history.
4. Approve each retained item. Review the entire source and check the acknowledgement. Choose "Profile 확정"; status becomes CONFIRMED. Refresh preserves the active local session.
5. Select submission files and execute preflight. The confirmed canonical profile reaches orchestration. Generic verifiers are not implemented: REVIEW/EXTERNAL only, REVIEW_REQUIRED summary, no invented submission evidence or frozen engine SHA.
6. Recheck remains available. Editing an approved requirement invalidates profile activation and earlier results; review/confirm it again before validating.
7. Start a new session with fixtures/announcements/scanned.pdf. VISION_REQUIRED is visible, zero requirements are generated and confirmation is disabled.

The new files and expected outputs are same-session synthetic SELF-BENCHMARK material. Real local code/PDF/browser execution is ACTUAL TEST; it establishes integration, not independent extraction accuracy. No historical 39-case or actual Vision claim.
