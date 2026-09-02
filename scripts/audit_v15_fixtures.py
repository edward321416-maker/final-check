"""Independent ground-truth audit; never imports or calls the frozen validator."""
from pathlib import Path
import hashlib
import json
import subprocess
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
TEAM = "테스트어린이집"
PDF_NAME = f"{TEAM}_숏폼공모서류.pdf"
VIDEO_NAME = f"{TEAM}_숏폼영상.MP4"
SECTION_TEXT = {"application": "참가 신청서", "privacy": "개인정보 수집 이용 동의서",
                "portrait": "초상권 사용 동의서", "description": "출품 영상작품 설명서"}


def audit() -> dict:
    records = {}
    for case, duration, privacy in [("demo-broken", 61, False), ("demo-fixed", 45, True)]:
        directory = ROOT / "fixtures/v15" / case
        pdfs = list(directory.glob("*.pdf"))
        assert len(pdfs) == 1 and pdfs[0].name == PDF_NAME
        video = directory / VIDEO_NAME
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(video)],
                               capture_output=True, text=True, encoding="utf-8", timeout=20, check=True)
        data = json.loads(probe.stdout)
        stream = next(item for item in data["streams"] if item["codec_type"] == "video")
        assert float(data["format"]["duration"]) == duration
        assert (stream["width"], stream["height"]) == (1080, 1920)
        assert stream["width"] / stream["height"] == 9 / 16
        assert "mp4" in data["format"]["format_name"] and video.suffix.lower() == ".mp4"
        assert video.stat().st_size < 300 * 1024 * 1024
        reader = PdfReader(pdfs[0])
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages)
        compact = "".join(text.split())
        presence = {key: "".join(value.split()) in compact for key, value in SECTION_TEXT.items()}
        assert presence == {"application": True, "privacy": privacy, "portrait": True, "description": True}
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"], check=True, timeout=90)
        records[case] = {"audit_pass": True, "video": {"filename": video.name, "duration_seconds": duration,
                         "width": stream["width"], "height": stream["height"], "ratio": "9:16",
                         "container": data["format"]["format_name"], "bytes": video.stat().st_size,
                         "sha256": hashlib.sha256(video.read_bytes()).hexdigest(), "full_decode": "PASS",
                         "fps": stream["avg_frame_rate"]},
                         "pdf": {"filename": pdfs[0].name, "count": 1, "page_count": len(pages),
                                 "section_presence": presence, "page_text": pages,
                                 "sha256": hashlib.sha256(pdfs[0].read_bytes()).hexdigest()}}
    result = {"audit_method": "Independent ffprobe/filesystem/pypdf; completed before validator scoring",
              "historical_corpus": False, "cases": records}
    (ROOT / "artifacts/demo-fixture-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    audit()
    print("PASS: both new packages match all intended video/PDF facts before scoring.")
