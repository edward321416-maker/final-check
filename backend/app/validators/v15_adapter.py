"""Application adaptation only. The imported frozen engine is never patched or reformatted."""
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys

from app.models.schemas import CheckSession, Evidence, FindingStatus, Requirement, SubmissionFile, ValidationResult

EXPECTED_SHA256 = "4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11"
FROZEN = Path(__file__).with_name("frozen_v15") / "validator_v1_5.py"
PROFILE = "frozen_v15"
TIMEOUT_SECONDS = 180
TITLES = {
    "R05": "제출서류 PDF 존재", "R06": "영상작품 존재", "R07": "제출서류 PDF 1개",
    "R08": "제출서류 파일명", "R09": "참가 신청서 및 개인정보 동의서",
    "R10": "초상권 사용 동의서", "R11": "출품 영상작품 설명서", "R12": "영상작품 파일명",
    "R13": "영상 길이 30~60초", "R14": "영상 해상도 1080×1920 이상", "R15": "세로형 영상 9:16",
    "R16": "MP4 컨테이너", "R17": "영상 파일 300MB 이하", "R19": "사진만으로 구성된 영상 확인",
    "R20": "외부 소스 라이선스", "R21": "생성형 AI 제작 여부",
}


class ValidatorUnavailable(RuntimeError):
    pass


class ValidatorRuntimeError(RuntimeError):
    pass


def frozen_engine():
    if hashlib.sha256(FROZEN.read_bytes()).hexdigest() != EXPECTED_SHA256:
        raise ValidatorUnavailable("Frozen Validator v1.5 SHA-256 mismatch")
    if not shutil.which("ffprobe"):
        raise ValidatorUnavailable("ffprobe is unavailable")
    return importlib.import_module("app.validators.frozen_v15.validator_v1_5")


def profile_requirements() -> list[Requirement]:
    engine = frozen_engine()
    return [Requirement(id=rid, title=TITLES[rid], description=quote,
                        verifier="EXTERNAL" if rid in {"R20", "R21"} else "VISION" if rid == "R19" else "SEMANTIC" if rid in {"R09", "R10", "R11"} else "DETERMINISTIC",
                        announcement_evidence=Evidence(source="동결 handoff 공고 발췌 · SOURCE_RULES",
                                                       locator=rid, excerpt=quote))
            for rid, quote in engine.SOURCE_RULES.items()]


def metadata(path: Path) -> SubmissionFile:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return SubmissionFile(name=path.name, size_bytes=path.stat().st_size, sha256=digest.hexdigest(),
                          media_type="application/pdf" if path.suffix.lower() == ".pdf" else "video/mp4")


@dataclass
class ValidationRun:
    raw: dict
    results: list[ValidationResult]
    complete: bool
    engine_sha256: str = EXPECTED_SHA256


class ValidatorV15Adapter:
    @property
    def available(self) -> bool:
        try:
            frozen_engine()
            return True
        except Exception:
            return False

    def require_available(self) -> None:
        try:
            frozen_engine()
        except Exception as error:
            raise ValidatorUnavailable("Frozen validator source, hash or runtime dependencies unavailable") from error

    def validate(self, session: CheckSession, package_dir: Path) -> ValidationRun:
        self.require_available()
        canonical = profile_requirements()
        if session.validation_profile != PROFILE or session.requirements != canonical:
            raise ValidatorUnavailable("The announcement has no verified frozen v1.5 requirement profile")
        paths = sorted(path for path in package_dir.iterdir() if path.is_file())
        actual = {path.name: (path.stat().st_size, metadata(path).sha256) for path in paths}
        if not session.files or {item.name: (item.size_bytes, item.sha256) for item in session.files} != actual:
            raise ValidatorRuntimeError("Submission bytes do not match the selected package")
        # Spawn the SAME Python runtime with UTF-8; do not alter imported engine globals.
        try:
            process = subprocess.run(
                [sys.executable, "-X", "utf8", "-m", "app.validators.v15_adapter", "--worker", str(package_dir)],
                cwd=Path(__file__).resolve().parents[2], capture_output=True,
                text=True, encoding="utf-8", timeout=TIMEOUT_SECONDS,
                env={**os.environ, "PYTHONUTF8": "1"},
            )
        except (subprocess.TimeoutExpired, OSError) as error:
            raise ValidatorRuntimeError("Frozen validator timed out or could not start") from error
        if process.returncode != 0 or len(process.stdout) > 8 * 1024 * 1024:
            raise ValidatorRuntimeError("Frozen validator execution failed; no READY result was produced")
        try:
            raw = json.loads(process.stdout)
            return self.adapt(session.requirements, raw, package_dir)
        except (ValueError, KeyError, TypeError) as error:
            raise ValidatorRuntimeError("Frozen validator returned invalid or unsupported output") from error

    def adapt(self, requirements: list[Requirement], raw: dict, package_dir: Path) -> ValidationRun:
        engine = frozen_engine()
        if not isinstance(raw, dict) or not isinstance(raw.get("findings"), list):
            raise ValidatorRuntimeError("Missing frozen findings")
        for key in ("blocker_rule_ids", "review_rule_ids", "vision_pending"):
            if not isinstance(raw.get(key), list):
                raise ValidatorRuntimeError("Incomplete frozen run")
        groups = defaultdict(list)
        for finding in raw["findings"]:
            if finding.get("requirement_id") not in engine.SOURCE_RULES or finding.get("status") not in {"BLOCKER", "REVIEW", "VISION_PENDING"}:
                raise ValidatorRuntimeError("Unknown frozen finding")
            groups[finding["requirement_id"]].append(finding)
        for status, key in (("BLOCKER", "blocker_rule_ids"), ("REVIEW", "review_rule_ids")):
            expected = sorted({f["requirement_id"] for f in raw["findings"] if f["status"] == status})
            if raw[key] != expected:
                raise ValidatorRuntimeError("Inconsistent frozen summary")
        pdfs = sorted(package_dir.glob("*.pdf")) + sorted(package_dir.glob("*.PDF"))
        pdfs = list(dict.fromkeys(pdfs))
        all_files = sorted(p for p in package_dir.iterdir() if p.is_file())
        videos = [p for p in all_files if p.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv"}]
        pdfs = [p for p in all_files if p.suffix.lower() == ".pdf"]
        text = "\n".join(engine.pdf_text(p) for p in pdfs)
        readable = len(engine.normalize(text)) >= 40
        video = package_dir / engine.GOOD_VIDEO
        if not video.exists() and videos:
            video = videos[0]
        info = {}
        if video.exists():
            try:
                probe = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(video)],
                                       capture_output=True, text=True, encoding="utf-8", timeout=20, check=True)
                info = json.loads(probe.stdout)
            except (subprocess.SubprocessError, ValueError, OSError):
                info = {}
        stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
        video_readable = bool(stream.get("width") and stream.get("height") and info.get("format", {}).get("duration"))
        file_list = ", ".join(f"{p.name} ({p.stat().st_size} bytes)" for p in all_files) or "제출파일 없음"
        pdf_evidence = Evidence(source=", ".join(p.name for p in pdfs) or "제출파일 목록",
                                locator="PDF 전체 추출 텍스트",
                                excerpt=f"추출 문자수 {len(text)}. " + (" ".join(text.split())[:900] or "텍스트 없음; Vision 확인 필요"))
        video_evidence = Evidence(source=video.name if video.exists() else "제출파일 목록",
                                  locator="실제 ffprobe / 파일 측정",
                                  excerpt=json.dumps({"duration_seconds": info.get("format", {}).get("duration"),
                                                      "width": stream.get("width"), "height": stream.get("height"),
                                                      "container": info.get("format", {}).get("format_name"),
                                                      "bytes": video.stat().st_size if video.exists() else None}, ensure_ascii=False))
        inventory = Evidence(source="실제 업로드 패키지", locator="전체 파일 목록 / 파일 수", excerpt=file_list)
        results = []
        complete = True
        for rule in requirements:
            rid = rule.id
            matched = groups[rid]
            status = FindingStatus.REVIEW
            message = "이 요구사항을 자동으로 확정할 근거가 충분하지 않습니다."
            action = "제출 원본과 공고를 직접 확인하세요."
            evidence = inventory if rid in {"R05", "R06", "R07", "R08", "R12"} else pdf_evidence if rid in {"R09", "R10", "R11"} else video_evidence
            if matched:
                quotes_ok = all(f.get("evidence_quote", "").strip() == rule.announcement_evidence.excerpt for f in matched)
                is_pending = any(f["status"] == "VISION_PENDING" for f in matched)
                status = FindingStatus.BLOCKER if any(f["status"] == "BLOCKER" for f in matched) and quotes_ok else FindingStatus.REVIEW
                message = " ".join(f.get("message", "확인 필요") for f in matched)
                if not quotes_ok:
                    complete = False
                    message = "공고 근거가 일치하지 않아 REVIEW로 보류했습니다. " + message
                if is_pending:
                    complete = False
                    status = FindingStatus.REVIEW
                    message = "이미지형 PDF: 실제 Vision 서비스가 연결되지 않아 문서 섹션 확인을 REVIEW로 보류합니다."
                detail = [{k: v for k, v in f.get("details", {}).items() if k not in {"vision_pages", "error"}} for f in matched]
                if rid == "R19":
                    evidence = Evidence(source=video.name, locator="동결 v1.5 영상 프레임 분석", excerpt=json.dumps(detail, ensure_ascii=False))
                action = "영상 길이를 30~60초로 수정하세요." if rid == "R13" else "참가 신청서와 개인정보 수집·이용 동의서를 PDF에 포함하세요." if rid == "R09" else action
            else:
                safe = {
                    "R05": bool(pdfs), "R06": bool(videos), "R07": len(pdfs) == 1,
                    "R08": (package_dir / engine.GOOD_PDF).is_file(),
                    "R09": readable and all(engine.contains_concept(text, engine.CONCEPT_TOKENS[key]) for key in ("application", "privacy")),
                    "R10": readable and engine.contains_concept(text, engine.CONCEPT_TOKENS["portrait"]),
                    "R11": readable and engine.contains_concept(text, engine.CONCEPT_TOKENS["description"]),
                    "R12": (package_dir / engine.GOOD_VIDEO).is_file(),
                    **{key: video_readable for key in ("R13", "R14", "R15", "R16", "R17", "R19")},
                }.get(rid, False)
                if safe:
                    status = FindingStatus.PASS
                    message = "동결 v1.5 실행에서 해당 조건의 위반이 없고, 실제 파일 측정 근거가 확인되었습니다."
                    if rid in {"R09", "R10", "R11"}:
                        message = "원본 PDF 추출 텍스트에서 필수 섹션 문구가 확인되었습니다. 서명·내용의 진위를 검증한 결과는 아닙니다."
                    action = "이 검사항목에서 추가 수정 없음"
                elif rid not in {"R20", "R21"}:
                    complete = False
            if rid in {"R19", "R20", "R21"} and status == FindingStatus.BLOCKER:
                status = FindingStatus.REVIEW
                complete = False
            if rid in {"R20", "R21"}:
                status = FindingStatus.REVIEW
                action = "라이선스 증빙을 직접 확인하세요." if rid == "R20" else "제작 과정과 AI 사용 내역을 직접 확인하세요."
                if not matched:
                    message = "제출파일만으로 자동 검증할 수 없는 항목입니다."
                evidence = Evidence(source="제출파일 검증 범위", locator="자동 검증 미지원",
                                    excerpt="라이선스 보유 또는 AI 제작 과정을 제출파일만으로 신뢰성 있게 확정할 수 없습니다.")
            results.append(ValidationResult(id=f"v15-{rid}", requirement_id=rid, status=status, title=rule.title,
                                            explanation=message, action=action, announcement_evidence=rule.announcement_evidence,
                                            submission_evidence=evidence, source_mode="validator"))
        return ValidationRun(raw=raw, results=results, complete=complete)


validator_v15 = ValidatorV15Adapter()

if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "--worker":
        raise SystemExit("Internal worker only")
    with redirect_stdout(sys.stderr):
        result = frozen_engine().validate_case(Path(sys.argv[2]))
    print(json.dumps(result, ensure_ascii=False))
