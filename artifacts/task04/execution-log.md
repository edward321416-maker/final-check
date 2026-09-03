# TASK 04 actual execution log

All times below are UTC unless marked otherwise. Commands ran in the dedicated
`D:/Users/admin/Desktop/ai공모전/해커톤/final-check` checkout (backend/frontend
subdirectory where stated). No benchmark extractor invocation occurred before Gold.

| Phase / actual command | Actual outcome |
|---|---|
| `gh pr view 2 --repo edward321416-maker/final-check --json state,mergedAt,mergeCommit,url` | MERGED at 2026-09-03T11:27:20Z; merge81bf2551c5967836d3e54869de2e86261428c78e |
| `git fetch origin`; ancestor check; `git switch main`; `git pull --ff-only origin main`; status | Main/origin matched expected commit; already up to date; clean before branch |
| `git switch -c codex/task-04-independent-extractor-benchmark` | Branch created from verified main |
| Source SHA capture | 2026-09-03T11:32:03.0726343Z; frozen/extractor/profile hashes saved |
| `backend/.venv/Scripts/python.exe -X utf8 scripts/collect_task04_sources.py` | Eight actual snapshots ultimately captured; one initial HTTP404 candidate replaced before annotation; linked JCIA PDF acquired |
| `backend/.venv/Scripts/python.exe -X utf8 scripts/scope_task04_sources.py` | Four whole PDFs and four complete HTML article bodies scoped; no semantic text repair |
| Local PyMuPDF render + actual image inspection | C01p1, C05p1, C07p4, C08p2 checked; four PNGs retained |
| Manual annotation then `backend/.venv/Scripts/python.exe -X utf8 scripts/freeze_task04_gold.py` | 173 Gold / eight cases; freeze11:46:35.794398; SHA035ebc06d3d62db6ab9c47c53d30cbc206be02667d845e9db59da6b9c5f7fe89 |
| `git commit` Gold; preserve raw HTML bytes with -text and second commit | 5d4bb99 then 978b911f3230ab00c995426e9ccf3c806ae8b3c5, both before baseline |
| Initial `backend/.venv/Scripts/python.exe -X utf8 scripts/run_task04_benchmark.py` | 11:49:12.725398: eight capture-serialization errors, no saved candidates; retained separately and UNSCORED |
| Same command after wrapper-only model_dump fix | 11:49:55.205838: eight actual cases, 211 candidates /211 gate accepted; unchanged product source |
| Manual candidates.tsv + misses.tsv; same runner command | All211 candidate rows /173 Gold covered;32 unique MATCH,65 partial-only,76 uncovered; aggregate metrics and pairs generated |
| Subsequent runner invocations | Hash-verified saved output reuse, not extractor reruns; Git freeze-byte check passed,35 first-occurrence anchor mismatches verified |
| Backend `.venv/Scripts/python.exe -X utf8 -m pytest -q --junitxml=../artifacts/task04/backend-tests.xml` | Exit0;47 passed in11.94s;one Starlette/httpx deprecation warning |
| Frontend `npm run typecheck` | Exit0;PASS |
| Frontend `npm run build` | Exit0;PASS;five product routes plus not-found generated |
| `scripts/stop-local.ps1` then frontend `npm run test:smoke` | Recorded own launcher stopped; actual Chromium desktop/mobile14 passed in21.5s;JSON copied to TASK04 |
| Preserve regression output / restore historical artifact files | Four generated TASK03 JSON files copied to TASK04; original tracked versions restored. Browser JSON copied, historical tracked JSON restored |
| Source-after / product diff audit | Frozen SHA identical; extractor/profile hashes unchanged; no backend/frontend/fixture/product-lock diff |

`git diff --check` passed after documentation changes. The first complete PR-range
whitespace check flagged tool-emitted trailing spaces/blank endings in build and
typecheck logs; its output is retained as diff-check-initial.log. Actual logs and
original HTML/PDF-derived input snapshots are exempt from whitespace lint, preserving
evidence bytes and frozen SHA. Product code has no such exemption. The complete
PR-range diff check was then rerun successfully (empty diff-check.log, exit0).
Final commit and PR state are added at publication. No TASK05 execution.
Gold protocol remained unchanged throughout. No dependency/provider was installed.
Raw backend/browser/build/typecheck/scoring logs and actual JSON/XML are adjacent.
