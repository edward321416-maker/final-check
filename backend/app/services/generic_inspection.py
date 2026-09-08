"""Deterministic inspection of application-owned PDF/MP4 submission bytes."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pypdf import PdfReader

from app.models.schemas import Evidence, SubmissionFile
from app.models.verifier_plans import GatedVerificationPlan


@dataclass(frozen=True)
class CheckerOutcome:
    status: str
    measured_fact: str
    submission_evidence: Evidence | None


@dataclass(frozen=True)
class TypeInspection:
    status: Literal["MATCH", "MISMATCH", "REVIEW"]
    fact: str


def inspect_submission(package: Path) -> list[SubmissionFile]:
    if not package.is_dir():
        raise ValueError("Application-owned submission package is unavailable")
    result: list[SubmissionFile] = []
    for path in sorted((item for item in package.iterdir() if item.is_file()), key=lambda item: item.name.casefold()):
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while chunk := stream.read(64 * 1024):
                digest.update(chunk)
        result.append(SubmissionFile(
            name=path.name,
            size_bytes=path.stat().st_size,
            media_type="application/pdf" if path.suffix.casefold() == ".pdf" else "video/mp4",
            sha256=digest.hexdigest(),
        ))
    return result


def _evidence(paths: list[Path], fact: str, locator: str) -> Evidence:
    names = ", ".join(path.name for path in paths) if paths else "제출 패키지"
    return Evidence(source=names, locator=locator, excerpt=fact)


def _compare(actual: float | int | str, operator: str, expected: float | int | str) -> bool:
    if operator == "EQ":
        return str(actual).casefold() == str(expected).casefold() if isinstance(actual, str) else actual == expected
    if operator == "LT":
        return actual < expected
    if operator == "LTE":
        return actual <= expected
    if operator == "GT":
        return actual > expected
    if operator == "GTE":
        return actual >= expected
    if operator == "EXACT_LITERAL":
        return str(actual) == str(expected)
    if operator == "PREFIX_LITERAL":
        return str(actual).startswith(str(expected))
    if operator == "SUFFIX_LITERAL":
        return str(actual).endswith(str(expected))
    if operator == "CONTAINS_LITERAL":
        return str(expected) in str(actual)
    raise ValueError("Unsupported closed operator")


def _select(plan: GatedVerificationPlan, package: Path) -> tuple[list[Path], str | None]:
    files = [path for path in package.iterdir() if path.is_file()]
    selector = plan.target_selector
    if selector.kind == "ALL_FILES":
        return sorted(files), None
    if selector.kind == "ALL_BY_EXTENSION":
        return sorted(path for path in files if path.suffix.casefold() == selector.value), None
    if selector.kind == "EXACT_NAME":
        matches = [path for path in files if path.name == selector.value]
        return matches, None if len(matches) == 1 else "TARGET_MISSING"
    matches = [path for path in files if path.suffix.casefold() == selector.value]
    return matches, None if len(matches) == 1 else "TARGET_AMBIGUOUS"


def _numeric_result(paths: list[Path], field: str, actual: int | float, plan: GatedVerificationPlan) -> CheckerOutcome:
    expected = plan.constraint.value
    fact = f"{field}={actual}; expected {plan.constraint.operator} {expected} {plan.constraint.unit}"
    status = "PASS" if _compare(actual, plan.constraint.operator, expected) else "VIOLATION"
    return CheckerOutcome(status, fact, _evidence(paths, fact, "deterministic checker"))


def _probe(path: Path) -> dict:
    executable = shutil.which("ffprobe")
    if not executable:
        raise RuntimeError("FFPROBE_UNAVAILABLE")
    completed = subprocess.run(
        [executable, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    if completed.returncode != 0:
        raise RuntimeError("FFPROBE_UNREADABLE")
    payload = json.loads(completed.stdout)
    videos = [stream for stream in payload.get("streams", []) if stream.get("codec_type") == "video"]
    if not videos or not isinstance(payload.get("format"), dict):
        raise RuntimeError("FFPROBE_MALFORMED")
    return {"stream": videos[0], "format": payload["format"]}


def _inspect_declared_type(path: Path, expected: str | None = None) -> TypeInspection:
    declared = (expected or path.suffix.lstrip(".")).casefold()
    if declared == "pdf":
        try:
            with path.open("rb") as stream:
                signature = stream.read(5)
        except OSError:
            return TypeInspection("REVIEW", f"{path.name}: PDF bytes unavailable")
        if signature != b"%PDF-":
            return TypeInspection("MISMATCH", f"{path.name}: PDF signature mismatch")
        try:
            PdfReader(path)
        except Exception:
            return TypeInspection("REVIEW", f"{path.name}: PDF parser could not confirm type")
        return TypeInspection("MATCH", f"{path.name}: PDF signature and parser confirmed")
    if declared == "mp4":
        try:
            data = _probe(path)
            media_format = data.get("format")
            format_name = media_format.get("format_name") if isinstance(media_format, dict) else None
            if not isinstance(format_name, str) or not format_name.strip():
                return TypeInspection("REVIEW", f"{path.name}: ffprobe returned no trusted container")
        except Exception:
            return TypeInspection("REVIEW", f"{path.name}: ffprobe could not confirm type")
        containers = {item.strip() for item in format_name.casefold().split(",")}
        if "mp4" in containers:
            return TypeInspection("MATCH", f"{path.name}: ffprobe container={format_name}")
        return TypeInspection("MISMATCH", f"{path.name}: ffprobe container={format_name}")
    return TypeInspection("REVIEW", f"{path.name}: unsupported declared type")


def confirm_pdf_type(path: Path) -> TypeInspection:
    return _inspect_declared_type(path, "PDF")


def _type_boundary(files: list[Path]) -> CheckerOutcome | None:
    inspections = [_inspect_declared_type(path) for path in files]
    if all(item.status == "MATCH" for item in inspections):
        return None
    fact = "; ".join(item.fact for item in inspections)
    return CheckerOutcome("REVIEW", fact, _evidence(files, fact, "declared-type trust boundary"))


def _targets_trusted_media_extension(plan: GatedVerificationPlan) -> bool:
    selector = plan.target_selector
    if selector.kind in {"UNIQUE_EXTENSION", "ALL_BY_EXTENSION"}:
        declared = str(selector.value or "").casefold()
    elif selector.kind == "EXACT_NAME":
        declared = Path(str(selector.value or "")).suffix.casefold()
    else:
        return False
    return declared in {".pdf", ".mp4"}


def run_checker(plan: GatedVerificationPlan, package: Path) -> CheckerOutcome:
    if plan.status != "VERIFIED":
        return CheckerOutcome("REVIEW", "Plan is not VERIFIED", None)
    if not package.is_dir():
        return CheckerOutcome("REVIEW", "Submission package unavailable", None)

    files, target_error = _select(plan, package)
    if plan.checker_type == "FILE_PRESENCE":
        if plan.target_selector.kind == "UNIQUE_EXTENSION" and len(files) > 1:
            return CheckerOutcome("REVIEW", "TARGET_AMBIGUOUS", _evidence(files, "target ambiguous", "actual file inventory"))
        type_review = _type_boundary(files) if files and _targets_trusted_media_extension(plan) else None
        if type_review:
            return type_review
        present = bool(files)
        expected = plan.constraint.value == "PRESENT"
        target = plan.target_selector.value or "all files"
        fact = f"{target}: present={str(present).lower()}"
        status = "PASS" if present == expected else "VIOLATION"
        return CheckerOutcome(status, fact, _evidence(files, fact, "actual file inventory"))
    if target_error:
        return CheckerOutcome("REVIEW", target_error, _evidence(files, target_error, "actual file inventory"))

    needs_type_boundary = (
        plan.checker_type in {"FILE_COUNT", "FILE_SIZE", "FILE_NAME"}
        and _targets_trusted_media_extension(plan)
    )
    if needs_type_boundary and files:
        type_review = _type_boundary(files)
        if type_review:
            return type_review

    if plan.checker_type == "FILE_COUNT":
        return _numeric_result(files, "file_count", len(files), plan)
    if not files:
        return CheckerOutcome("REVIEW", "TARGET_MISSING", _evidence([], "target missing", "actual file inventory"))

    if plan.checker_type == "FILE_NAME":
        matches = [_compare(path.name, plan.constraint.operator, plan.constraint.value) for path in files]
        fact = f"names={[path.name for path in files]}; expected {plan.constraint.operator} {plan.constraint.value}"
        return CheckerOutcome("PASS" if all(matches) else "VIOLATION", fact, _evidence(files, fact, "actual file inventory"))

    if plan.checker_type == "FILE_SIZE":
        comparisons: list[bool] = []
        ambiguous = False
        for path in files:
            size = path.stat().st_size
            if plan.constraint.unit == "BYTES":
                comparisons.append(_compare(size, plan.constraint.operator, plan.constraint.value))
            elif plan.constraint.unit == "MIB":
                comparisons.append(_compare(size, plan.constraint.operator, float(plan.constraint.value) * 1024 * 1024))
            else:
                decimal = _compare(size, plan.constraint.operator, float(plan.constraint.value) * 1_000_000)
                binary = _compare(size, plan.constraint.operator, float(plan.constraint.value) * 1024 * 1024)
                ambiguous = ambiguous or decimal != binary
                comparisons.append(decimal and binary)
        fact = f"sizes_bytes={{{', '.join(f'{p.name}:{p.stat().st_size}' for p in files)}}}; expected {plan.constraint.operator} {plan.constraint.value} {plan.constraint.unit}"
        if ambiguous:
            return CheckerOutcome("REVIEW", fact + "; decimal/binary interpretation differs", _evidence(files, fact, "exact byte measurement"))
        return CheckerOutcome("PASS" if all(comparisons) else "VIOLATION", fact, _evidence(files, fact, "exact byte measurement"))

    if plan.checker_type == "PDF_PAGE_COUNT":
        try:
            counts = [len(PdfReader(path).pages) for path in files]
        except Exception:
            return CheckerOutcome("REVIEW", "PDF parser could not produce a page count", _evidence(files, "parser failure", "pypdf"))
        return _numeric_result(files, "pdf_page_count", sum(counts), plan)

    if plan.checker_type == "FILE_TYPE":
        expected = str(plan.constraint.value).upper()
        inspections = [_inspect_declared_type(path, expected) for path in files]
        fact = "; ".join(item.fact for item in inspections)
        if any(item.status == "REVIEW" for item in inspections):
            return CheckerOutcome("REVIEW", fact, _evidence(files, fact, "signature/parser/ffprobe type inspection"))
        status = "PASS" if all(item.status == "MATCH" for item in inspections) else "VIOLATION"
        return CheckerOutcome(status, fact, _evidence(files, fact, "signature/parser/ffprobe type inspection"))

    if plan.checker_type == "VIDEO_METADATA":
        try:
            data = _probe(files[0])
            stream, media_format = data["stream"], data["format"]
            field = plan.constraint.field
            if field == "DURATION_SECONDS":
                actual: int | float | str = float(stream.get("duration") or media_format["duration"])
            elif field == "WIDTH":
                actual = int(stream["width"])
            elif field == "HEIGHT":
                actual = int(stream["height"])
            elif field == "ASPECT_RATIO":
                expected = plan.constraint.value
                if isinstance(expected, str) and ":" in expected:
                    left, right = expected.split(":", 1)
                    expected = float(left) / float(right)
                actual = float(stream["width"]) / float(stream["height"])
                adjusted = plan.model_copy(deep=True)
                adjusted.constraint.value = expected
                return _numeric_result(files, "aspect_ratio", actual, adjusted)
            else:
                actual = str(media_format.get("format_name", ""))
                expected = str(plan.constraint.value).casefold()
                passed = expected in actual.casefold() if expected == "mp4" else actual.casefold() == expected
                fact = f"container={actual}; expected {expected}"
                return CheckerOutcome("PASS" if passed else "VIOLATION", fact, _evidence(files, fact, "ffprobe"))
            return _numeric_result(files, field.casefold(), actual, plan)
        except (OSError, KeyError, TypeError, ValueError, RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError):
            return CheckerOutcome("REVIEW", "ffprobe could not produce trusted metadata", _evidence(files, "ffprobe failure", "ffprobe"))

    return CheckerOutcome("REVIEW", "Unsupported checker", None)
