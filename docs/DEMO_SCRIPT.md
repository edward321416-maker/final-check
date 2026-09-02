# TASK 01 demo script
All findings in this script are MOCK. The announcement and submission package are synthetic.

1. Open http://127.0.0.1:3100. Read the visible demo label.
2. Click "demo 검사 시작하기". Announcement Analysis displays five requirements and announcement excerpts.
3. Click "제출파일 선택하기". On Submission Upload choose "문제 있는 demo 불러오기".
4. Confirm proposal.pdf and clip.mp4 are listed; consent.pdf is missing. Click "Preflight 실행하기".
5. Results: BLOCKED, two BLOCKERs, one REVIEW, one PASS, one EXTERNAL. Open/read both evidence columns. Filter BLOCKER, then return to all.
6. Click "수정 후 재검사". On Recheck choose "수정한 demo 불러오기".
7. Confirm consent.pdf has been added. Click "재검사 실행하기".
8. Results: two statuses change BLOCKER → PASS. The summary is NEEDS_REVIEW. R19 REVIEW and portal EXTERNAL remain.
9. Reload: session is restored from its opaque session ID while the backend is alive.

Custom-file branch: Home → select a PDF/TXT announcement → "파일 정보 확인" → Upload PDF/MP4 → run.
The server receives names, sizes and SHA-256 metadata; no real requirements/results are invented. Validation returns an explicit unavailable error and stays on Upload.
Restart or one hour of inactivity expires local sessions; the UI provides a route back Home.
