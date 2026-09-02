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
Arbitrary announcement upload remains unsupported for automatic extraction. No generic profile is invented.
Image-only PDFs are rendered by the frozen engine but stay REVIEW without a Vision provider.
