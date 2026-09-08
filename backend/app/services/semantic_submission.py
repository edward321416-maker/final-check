"""Prepare one bounded, trusted PDF text snapshot for semantic review."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from app.models.profiles import GenericRequirementProfile, ProfileRequirement
from app.models.semantic_review import SemanticCoverage
from app.services.generic_inspection import confirm_pdf_type


MAX_SEMANTIC_PAGES = 50
MAX_SEMANTIC_CHARS = 100_000
MAX_SEMANTIC_REQUIREMENTS = 50
DOCUMENT_ID = "D01"


@dataclass(frozen=True)
class SemanticPage:
    page_id: str
    page_number: int
    text: str
    text_sha256: str


@dataclass(frozen=True)
class SemanticPreparation:
    eligible_requirement_ids: tuple[str, ...]
    document_id: str
    actual_filename: str | None
    file_sha256: str | None
    coverage: SemanticCoverage
    pages: tuple[SemanticPage, ...]
    total_characters: int
    call_ai: bool
    reason_code: str | None


def eligible_semantic_requirements(profile: GenericRequirementProfile) -> list[ProfileRequirement]:
    return [
        item
        for item in profile.requirements
        if (
            item.authoritative
            and item.extraction_status == "CONFIRMED"
            and item.verifier == "SEMANTIC"
            and item.modality in {"MUST", "MUST_NOT"}
            and item.condition.strip().casefold() == "always"
        )
    ]


def _preparation(
    requirement_ids: tuple[str, ...],
    *,
    actual_filename: str | None = None,
    file_sha256: str | None = None,
    coverage: SemanticCoverage = "NONE",
    pages: tuple[SemanticPage, ...] = (),
    total_characters: int = 0,
    call_ai: bool = False,
    reason_code: str | None,
) -> SemanticPreparation:
    return SemanticPreparation(
        eligible_requirement_ids=requirement_ids,
        document_id=DOCUMENT_ID,
        actual_filename=actual_filename,
        file_sha256=file_sha256,
        coverage=coverage,
        pages=pages,
        total_characters=total_characters,
        call_ai=call_ai,
        reason_code=reason_code,
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(64 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_semantic_submission(profile: GenericRequirementProfile, package: Path) -> SemanticPreparation:
    requirements = eligible_semantic_requirements(profile)
    requirement_ids = tuple(item.requirement_id for item in requirements)
    if not requirement_ids:
        return _preparation(requirement_ids, reason_code="SEMANTIC_REQUIREMENTS_UNAVAILABLE")
    if len(requirement_ids) > MAX_SEMANTIC_REQUIREMENTS:
        return _preparation(requirement_ids, reason_code="SEMANTIC_INPUT_TOO_LARGE")

    pdfs = sorted(
        (path for path in package.iterdir() if path.is_file() and path.suffix.casefold() == ".pdf"),
        key=lambda path: path.name.casefold(),
    ) if package.is_dir() else []
    if not pdfs:
        return _preparation(requirement_ids, reason_code="SEMANTIC_TARGET_MISSING")
    if len(pdfs) > 1:
        return _preparation(requirement_ids, reason_code="SEMANTIC_TARGET_AMBIGUOUS")

    target = pdfs[0]
    try:
        file_sha256 = _file_sha256(target)
    except OSError:
        return _preparation(requirement_ids, actual_filename=target.name, reason_code="SEMANTIC_TARGET_UNTRUSTED")
    if confirm_pdf_type(target).status != "MATCH":
        return _preparation(
            requirement_ids,
            actual_filename=target.name,
            file_sha256=file_sha256,
            reason_code="SEMANTIC_TARGET_UNTRUSTED",
        )

    try:
        document = pymupdf.open(target)
    except Exception:
        return _preparation(
            requirement_ids,
            actual_filename=target.name,
            file_sha256=file_sha256,
            reason_code="PDF_TEXT_EXTRACTION_FAILED",
        )
    try:
        if document.is_encrypted or len(document) > MAX_SEMANTIC_PAGES:
            return _preparation(
                requirement_ids,
                actual_filename=target.name,
                file_sha256=file_sha256,
                reason_code="PDF_TEXT_EXTRACTION_FAILED" if document.is_encrypted else "SEMANTIC_INPUT_TOO_LARGE",
            )
        pages: list[SemanticPage] = []
        total_characters = 0
        textless_pages = 0
        for page_number, page in enumerate(document, start=1):
            text = page.get_text()
            if not text.strip():
                textless_pages += 1
                continue
            total_characters += len(text)
            if total_characters > MAX_SEMANTIC_CHARS:
                return _preparation(
                    requirement_ids,
                    actual_filename=target.name,
                    file_sha256=file_sha256,
                    reason_code="SEMANTIC_INPUT_TOO_LARGE",
                )
            pages.append(SemanticPage(
                page_id=f"{DOCUMENT_ID}-P{page_number:03d}",
                page_number=page_number,
                text=text,
                text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            ))
    except Exception:
        return _preparation(
            requirement_ids,
            actual_filename=target.name,
            file_sha256=file_sha256,
            reason_code="PDF_TEXT_EXTRACTION_FAILED",
        )
    finally:
        document.close()

    if not pages:
        return _preparation(
            requirement_ids,
            actual_filename=target.name,
            file_sha256=file_sha256,
            reason_code="TEXT_UNAVAILABLE",
        )
    coverage: SemanticCoverage = "PARTIAL" if textless_pages else "FULL"
    return _preparation(
        requirement_ids,
        actual_filename=target.name,
        file_sha256=file_sha256,
        coverage=coverage,
        pages=tuple(pages),
        total_characters=total_characters,
        call_ai=True,
        reason_code=None,
    )
