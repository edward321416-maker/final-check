"""Capture eight public source documents; never imports the product extractor."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import httpx
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "benchmarks/task04/sources"
CASES = [
    ("C01", "제2회 청렴 60초 영상 공모전", "경기도교육청", "PDF", "https://www.goe.go.kr/resource/old/BBSMSTR_000000000112/BBS_202503090616385901.pdf"),
    ("C02", "2025년 기후·환경 숏폼 영상공모전", "시청자미디어재단 / 한국환경연구원", "HTML", "https://sotong.go.kr/front/epilogue/epilogueBbsViewPage.do?bbs_id=8ad235b5e1f045b5b2c3715d2c072aff&miv_pageNo=20&searchkey=A&searchtxt="),
    ("C03", "2025 KIBS-HUSS 융합캠프(인사이트) 해커톤", "국민대학교 KIBS", "HTML", "https://kibs.kookmin.ac.kr/notice/91"),
    ("C04", "2025 금융 AI Challenge: 금융 AI 모델 경쟁", "금융보안원 / DACON", "HTML", "https://www.dacon.io/competitions/official/236527/overview/rules"),
    ("C05", "제8회 기상·기후테크 창업 아이디어 공모전", "부산지방기상청 외", "PDF", "https://www.kma.go.kr/kma/servlet/NeoboardProcess?bid=gongzi&callback=https://www.kma.go.kr/kma/news/notice.jsp&fno=2&k=ATC202504221524372_b5c16558-e010-4c7e-a4cb-20cbf9e1b184.pdf&mode=download&num=1193622&ses=USERSESSION"),
    ("C06", "제4회 융·복합 데이터 활용 창업 경진대회", "한국저작권위원회 / 컨소시엄", "HTML", "https://www.copyright.or.kr/notify/notice/view.do?brdctsno=54044"),
    ("C07", "2025 상주세계모자페스티벌 대표프로그램 아이디어 공모전", "상주시", "PDF", "https://www.sangju.go.kr/swhf/file/readFile.tc?fileId=FL00000000557&fileNo=1"),
    ("C08", "2025 전라남도 공공·빅데이터 활용 아이디어 공모전", "전라남도 / 전남정보문화산업진흥원", "PDF", "https://www.jcia.or.kr/async/MultiFile/download.do?FS_KEYNO=FS_0000013358"),
]


class BodyText(HTMLParser):
    """Visible text with structural block breaks; no semantic normalization."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in {"script", "style", "noscript"}:
            self.hidden += 1
        if not self.hidden and tag in {"br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self.hidden = max(0, self.hidden - 1)
        if not self.hidden and tag in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")
        if not self.hidden and tag in {"td", "th"}:
            self.parts.append(" | ")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(re.sub(r"\s+", " ", data))

    def text(self) -> str:
        return "\n".join(line.strip() for line in "".join(self.parts).splitlines() if line.strip())


def main() -> None:
    if (OUT.parent / "gold_manifest.json").exists():
        raise RuntimeError("Corpus is frozen; collection is disabled")
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    error_path = ROOT / "artifacts/task04/collection-errors.json"
    attempts = json.loads(error_path.read_text(encoding="utf-8")) if error_path.exists() else []
    with httpx.Client(follow_redirects=True, timeout=45) as client:
        for cid, title, org, kind, url in CASES:
            path = OUT / f"{cid}.{kind.lower()}"
            captured_at = datetime.now(timezone.utc).isoformat()
            resolved_url = url
            if path.exists():
                raw = path.read_bytes()
                captured_at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
            else:
                try:
                    response = client.get(url)
                    response.raise_for_status()
                except httpx.HTTPError as exc:
                    attempts.append({"case_id": cid, "url": url, "at": captured_at, "error": str(exc)})
                    print(f"{cid}: unavailable; recorded collection error")
                    continue
                raw = response.content
                resolved_url = str(response.url)
                path.write_bytes(raw)
            if kind == "PDF":
                with pymupdf.open(path) as doc:
                    content = "\n".join(page.get_text() for page in doc)
            else:
                parser = BodyText()
                parser.feed(raw.decode("utf-8"))
                content = parser.text()
            (OUT / f"{cid}.unscoped.txt").write_text(content, encoding="utf-8", newline="\n")
            records.append({"case_id": cid, "title": title, "organization": org,
                            "source_url": url, "resolved_url": resolved_url,
                            "retrieved_at": captured_at,
                            "source_type": kind, "source_sha256": hashlib.sha256(raw).hexdigest(),
                            "snapshot_path": str(path.relative_to(ROOT)).replace("\\", "/")})
            print(f"{cid}: captured {len(raw)} bytes; {len(content)} text characters")
    (OUT.parent / "manifest.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    error_path.write_text(json.dumps(attempts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
