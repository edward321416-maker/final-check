# TASK 03 synthetic announcement fixtures

- submission.txt: new Korean submission-condition text, created for this integration task.
- submission.pdf: actual text-based PDF generated from that text, with an embedded Unicode-capable font.
- scanned.pdf: actual raster-only rendering of the same content; no text layer.

Generate with scripts/generate_announcement_fixtures.py. The generator checks PDF content with pypdf, separately from the application's PyMuPDF ingestion worker. Hashes and byte sizes are recorded in artifacts/task03/announcement-fixture-audit.json.
These are synthetic integration fixtures, not a real competition notice, independent gold set or historical 39-case corpus. Expected extraction and input were authored together: **SELF-BENCHMARK** only. Running the actual file/code paths is **ACTUAL TEST**.
