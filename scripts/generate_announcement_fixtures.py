"""New TASK 03 synthetic files, not an independent or historical benchmark."""
import hashlib
import json
from pathlib import Path
import pymupdf
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "fixtures" / "announcements"


def main() -> None:
    text = (BASE / "submission.txt").read_text(encoding="utf-8")
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_font(fontname="fixture_cjk", fontbuffer=pymupdf.Font("cjk").buffer)
        for i, line in enumerate(text.splitlines()):
            page.insert_text((35, 50 + i * 32), line, fontname="fixture_cjk", fontsize=10)
        doc.save(BASE / "submission.pdf", deflate=True)
        with pymupdf.open() as scan:
            target = scan.new_page()
            target.insert_image(target.rect, stream=page.get_pixmap().tobytes("png"))
            scan.save(BASE / "scanned.pdf", deflate=True)
    extracted = "\n".join(p.extract_text() or "" for p in PdfReader(BASE / "submission.pdf").pages)
    scanned = "".join(p.extract_text() or "" for p in PdfReader(BASE / "scanned.pdf").pages)
    assert "제안서는 PDF 형식으로 제출해야 한다." in extracted
    assert "10페이지" in extracted and "파일명" in extracted
    assert not scanned.strip()
    audit = {"classification": "ACTUAL TEST / same-session synthetic fixtures", "accuracy_evaluation": "SELF-BENCHMARK only",
             "text_pdf_extractable": True, "scan_text_empty": True,
             "files": [{"name": p.name, "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                       for p in sorted(BASE.iterdir()) if p.suffix in {".txt", ".pdf"}]}
    (ROOT / "artifacts/task03/announcement-fixture-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ACTUAL TEST: text PDF and raster-only PDF generated; independent pypdf byte-content checks passed.")


if __name__ == "__main__":
    main()
