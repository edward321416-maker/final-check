"""Bounded local text/PDF ingestion. No OCR, network or Vision inference."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from app.models.profiles import AnnouncementSource

MAX_ANNOUNCEMENT_BYTES = 10 * 1024 * 1024
MAX_TEXT = 100_000
MAX_PAGES = 50


def source_from_bytes(name: str, data: bytes, source_type: str, path: Path | None = None) -> AnnouncementSource:
    if not data or len(data) > MAX_ANNOUNCEMENT_BYTES:
        raise ValueError("공고 파일은 비어 있지 않은 10 MiB 이하 파일이어야 합니다.")
    status, notice, pages, text = "READABLE", "", None, ""
    if source_type == "TEXT":
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            status, notice = "UNREADABLE", "UTF-8 텍스트를 입력해 주세요. 내용을 추정하지 않았습니다."
    else:
        if path is None:
            raise ValueError("PDF input needs an isolated source file")
        try:
            result = subprocess.run(
                [sys.executable, "-X", "utf8", "-m", "app.services.announcement_input", str(path)],
                cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, encoding="utf-8", timeout=30,
            )
            parsed = json.loads(result.stdout) if result.returncode == 0 else {}
            text, pages = parsed.get("text", ""), parsed.get("pages")
            status, notice = parsed.get("status", "UNREADABLE"), parsed.get("notice", "PDF를 읽지 못했습니다. 내용을 추정하지 않았습니다.")
        except (subprocess.TimeoutExpired, ValueError):
            status, notice = "UNREADABLE", "PDF 처리에 실패했습니다. 텍스트 공고를 직접 입력해 주세요."
    if len(text) > MAX_TEXT:
        text, status, notice = "", "UNSUPPORTED", "공고 텍스트는 100,000자 이하만 지원합니다."
    if not text.strip() and status == "READABLE":
        status, notice = "UNREADABLE", "읽을 수 있는 텍스트가 없습니다. 내용을 추정하지 않았습니다."
    return AnnouncementSource(source_type=source_type, name=name, sha256=hashlib.sha256(data).hexdigest(),
                              text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(), text=text,
                              ingestion_status=status, notice=notice, page_count=pages)


def pdf_worker(path: Path) -> dict:
    import pymupdf
    try:
        with pymupdf.open(path) as doc:
            count = len(doc)
            if doc.needs_pass or count > MAX_PAGES:
                return {"status": "UNSUPPORTED", "notice": "암호화 PDF 또는 50페이지 초과 PDF는 지원하지 않습니다.", "pages": count}
            chunks: list[str] = []
            total = 0
            for page in doc:
                chunk = page.get_text()
                total += len(chunk) + 1
                if total > MAX_TEXT:
                    return {"status": "UNSUPPORTED", "notice": "공고 텍스트는 100,000자 이하만 지원합니다.", "pages": count}
                chunks.append(chunk)
            partial = not chunks or any(not chunk.strip() for chunk in chunks)
            return {"text": "\n".join(chunks), "pages": count,
                    "status": "VISION_REQUIRED" if partial else "READABLE",
                    "notice": "텍스트 없는 페이지가 있습니다. Vision 미연결: 요구사항을 만들지 않습니다." if partial else "PDF 텍스트 순서를 원문과 직접 대조하세요. 이미지 속 조건은 읽지 못합니다."}
    except Exception:
        return {"status": "UNREADABLE", "notice": "PDF를 읽지 못했습니다. 내용을 추정하지 않았습니다."}


if __name__ == "__main__":
    print(json.dumps(pdf_worker(Path(sys.argv[1])), ensure_ascii=False))
