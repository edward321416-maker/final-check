"""One-time, explicit input scoping before Gold; no extractor dependency."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/task04"
# Keep one complete article copy, excluding navigation and attachment link lists.
BOUNDS = {
    "C02": ("「기후 · 환경 숏폼 영상 공모전」 공모", "[붙임1] 2025 기후·환경 숏폼 영상공모전 공고문.hwp"),
    "C03": ("미래 사회 문제 해결을 위한 인문사회 융합 아이디어톤,", "HUSS 인사이트 해커톤 신청서.hwp"),
    "C04": ("1. 참여\n", "개요 평가 규칙 일정 상금 동의사항"),
    "C06": ("[공모 요강]", "이전글 다음글"),
}


def main() -> None:
    if (BASE / "gold_manifest.json").exists():
        raise RuntimeError("Corpus is frozen; input scoping is disabled")
    records = json.loads((BASE / "manifest.json").read_text(encoding="utf-8"))
    assert len(records) == 8
    for case in records:
        cid = case["case_id"]
        text = (BASE / "sources" / f"{cid}.unscoped.txt").read_text(encoding="utf-8")
        if cid in BOUNDS:
            start, end = BOUNDS[cid]
            left = text.index(start)
            right = text.index(end, left)
            text = text[left:right].strip()
            case["scope"] = {"kind": "complete HTML article body, one responsive copy",
                             "start_inclusive": start, "end_exclusive": end,
                             "excluded": "site navigation, responsive duplicate, linked forms/posters/other tabs"}
        else:
            case["scope"] = {"kind": "complete attached PDF including forms", "excluded": "other linked documents"}
        dest = BASE / "sources" / f"{cid}.txt"
        dest.write_text(text, encoding="utf-8", newline="\n")
        case["input_path"] = dest.relative_to(ROOT).as_posix()
        case["input_sha256"] = hashlib.sha256(dest.read_bytes()).hexdigest()
        case["text_extraction"] = "PyMuPDF page.get_text(), newline-joined; same as application" if case["source_type"] == "PDF" else "stdlib HTMLParser block boundaries and whitespace collapse; explicit article scope"
        print(f"{cid}: {len(text)} characters, {len(text.splitlines())} lines")
    (BASE / "manifest.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
