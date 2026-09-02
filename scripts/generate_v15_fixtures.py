"""New TASK 02 real files; separate from the untouched TASK 01 skeleton fixtures."""
from pathlib import Path
import hashlib
import json
import subprocess
import fitz

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "fixtures/v15"
TEAM = "테스트어린이집"
PDF_NAME = f"{TEAM}_숏폼공모서류.pdf"
VIDEO_NAME = f"{TEAM}_숏폼영상.MP4"


def make_pdf(path: Path, privacy: bool, scanned: bool = False) -> None:
    headings = ["참가 신청서", "초상권 사용 동의서", "출품 영상작품 설명서"]
    if privacy:
        headings.insert(1, "개인정보 수집 이용 동의서")
    doc = fitz.open()
    korean_font = fitz.Font("cjk").buffer
    for heading in headings:
        page = doc.new_page()
        page.insert_font(fontname="demo_cjk", fontbuffer=korean_font)
        page.insert_text((50, 70), "FINAL CHECK / SYNTHETIC FIXTURE", fontsize=14)
        page.insert_text((50, 130), heading, fontname="demo_cjk", fontsize=20)
        page.insert_text((50, 180), "검증용 가상 서류입니다. 실제 신청 또는 법적 동의가 아닙니다.", fontname="demo_cjk", fontsize=12)
        page.insert_text((50, 230), "기관: 테스트어린이집 / 작성자: 가상 참가자", fontname="demo_cjk", fontsize=12)
    if scanned:
        image_doc = fitz.open()
        for page in doc:
            raster = page.get_pixmap(matrix=fitz.Matrix(1, 1))
            target = image_doc.new_page(width=page.rect.width, height=page.rect.height)
            target.insert_image(target.rect, stream=raster.tobytes("png"))
        doc.close()
        doc = image_doc
    doc.save(path, garbage=4, deflate=True)
    doc.close()


def main() -> None:
    for case, duration, privacy in [("demo-broken", 61, False), ("demo-fixed", 45, True)]:
        target = BASE / case
        target.mkdir(parents=True, exist_ok=True)
        make_pdf(target / PDF_NAME, privacy)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", f"color=c=0x52694d:size=1080x1920:rate=2:duration={duration}",
                        "-an", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", str(target / VIDEO_NAME)], check=True)
        print(f"Generated {case}: {duration}s, 1080x1920, MP4; privacy section={privacy}")
    print("These are new acceptance fixtures, not the historical 39-case corpus.")


if __name__ == "__main__":
    main()
