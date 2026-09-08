import hashlib
from pathlib import Path

import pymupdf

from app.models.profiles import AnnouncementSource, ExtractedRequirement, GenericRequirementProfile
from app.services import profiles
from app.services.semantic_submission import (
    confirm_pdf_type,
    eligible_semantic_requirements,
    prepare_semantic_submission,
)


def announcement(text: str = "PDF에 제출 내용을 포함해야 합니다.") -> AnnouncementSource:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return AnnouncementSource(
        source_type="TEXT",
        name="announcement.txt",
        sha256=digest,
        text_sha256=digest,
        text=text,
        ingestion_status="READABLE",
    )


def requirement(requirement_id: str, **overrides):
    source = announcement()
    values = {
        "requirement_id": requirement_id,
        "rule": "PDF must include the required content.",
        "modality": "MUST",
        "severity": "REVIEW",
        "verifier": "SEMANTIC",
        "condition": "always",
        "evidence": {"source_section": "Submission", "quote": source.text},
        "confidence": 1,
    }
    values.update(overrides)
    extracted = ExtractedRequirement(**values)
    item = profiles.anchor(extracted, source)
    item.extraction_status = "CONFIRMED"
    item.authoritative = True
    return item


def semantic_profile(items, *, status: str = "CONFIRMED") -> GenericRequirementProfile:
    source = announcement()
    profile = profiles.new_profile(source)
    profile.requirements = items
    profile.extraction_complete = True
    profile.status = status
    return GenericRequirementProfile.model_validate(profile.model_dump())


def write_pdf(path: Path, page_texts: list[str | None]) -> None:
    document = pymupdf.open()
    for text in page_texts:
        page = document.new_page()
        if text is not None:
            page.insert_text((72, 72), text)
    document.save(path)
    document.close()


def write_dense_text_pdf(path: Path, text: str) -> None:
    document = pymupdf.open()
    page = document.new_page(width=595, height=842)
    assert page.insert_textbox(pymupdf.Rect(1, 1, 594, 841), text, fontsize=1) >= 0
    document.save(path)
    document.close()


def test_only_confirmed_authoritative_mandatory_always_semantic_is_eligible():
    eligible = requirement("R01")
    unconfirmed = requirement("R02")
    unconfirmed.extraction_status = "EXTRACTED"
    unconfirmed.authoritative = False
    optional = requirement("R04", modality="SHOULD")
    conditional = requirement("R05", condition="when applicable")
    deterministic = requirement("R06", verifier="DETERMINISTIC")

    profile = semantic_profile([eligible, unconfirmed, optional, conditional, deterministic], status="DRAFT")

    assert [item.requirement_id for item in eligible_semantic_requirements(profile)] == ["R01"]


def test_zero_pdf_returns_target_missing_without_ai(tmp_path):
    preparation = prepare_semantic_submission(semantic_profile([requirement("R01")]), tmp_path)

    assert preparation.reason_code == "SEMANTIC_TARGET_MISSING"
    assert preparation.coverage == "NONE" and preparation.pages == ()
    assert preparation.call_ai is False


def test_two_pdf_returns_target_ambiguous_without_ai(tmp_path):
    write_pdf(tmp_path / "first.pdf", ["first"])
    write_pdf(tmp_path / "second.pdf", ["second"])

    preparation = prepare_semantic_submission(semantic_profile([requirement("R01")]), tmp_path)

    assert preparation.reason_code == "SEMANTIC_TARGET_AMBIGUOUS"
    assert preparation.call_ai is False


def test_fake_pdf_fails_type_trust_without_ai(tmp_path):
    fake = tmp_path / "submission.pdf"
    fake.write_text("not a PDF", encoding="utf-8")

    preparation = prepare_semantic_submission(semantic_profile([requirement("R01")]), tmp_path)

    assert confirm_pdf_type(fake).status == "MISMATCH"
    assert preparation.reason_code == "SEMANTIC_TARGET_UNTRUSTED"
    assert preparation.call_ai is False


def test_text_pdf_produces_page_ids_and_full_coverage(tmp_path):
    submission = tmp_path / "submission.pdf"
    write_pdf(submission, ["First required paragraph.", "Second required paragraph."])

    preparation = prepare_semantic_submission(semantic_profile([requirement("R01")]), tmp_path)

    assert preparation.document_id == "D01"
    assert [page.page_id for page in preparation.pages] == ["D01-P001", "D01-P002"]
    assert [page.text for page in preparation.pages] == ["First required paragraph.\n", "Second required paragraph.\n"]
    assert preparation.coverage == "FULL" and preparation.call_ai is True
    assert preparation.file_sha256 == hashlib.sha256(submission.read_bytes()).hexdigest()


def test_scanned_textless_pdf_returns_none_coverage(tmp_path):
    write_pdf(tmp_path / "scanned.pdf", [None])

    preparation = prepare_semantic_submission(semantic_profile([requirement("R01")]), tmp_path)

    assert preparation.coverage == "NONE" and preparation.reason_code == "TEXT_UNAVAILABLE"
    assert preparation.pages == () and preparation.call_ai is False


def test_partial_text_coverage_is_explicit(tmp_path):
    write_pdf(tmp_path / "partial.pdf", ["Readable content.", None])

    preparation = prepare_semantic_submission(semantic_profile([requirement("R01")]), tmp_path)

    assert preparation.coverage == "PARTIAL"
    assert [page.page_id for page in preparation.pages] == ["D01-P001"]
    assert preparation.call_ai is True


def test_over_50_pages_does_not_truncate(tmp_path):
    write_pdf(tmp_path / "long.pdf", ["page"] * 51)

    preparation = prepare_semantic_submission(semantic_profile([requirement("R01")]), tmp_path)

    assert preparation.reason_code == "SEMANTIC_INPUT_TOO_LARGE"
    assert preparation.pages == () and preparation.call_ai is False


def test_over_100k_chars_does_not_truncate(tmp_path):
    write_dense_text_pdf(tmp_path / "large.pdf", ("x" * 2000 + "\n") * 50)

    preparation = prepare_semantic_submission(semantic_profile([requirement("R01")]), tmp_path)

    assert preparation.reason_code == "SEMANTIC_INPUT_TOO_LARGE"
    assert preparation.pages == () and preparation.total_characters == 0
    assert preparation.call_ai is False


def test_51_eligible_requirements_do_not_batch_or_call_ai(tmp_path):
    write_pdf(tmp_path / "submission.pdf", ["Readable content."])
    profile = semantic_profile([requirement(f"R{index:02d}") for index in range(1, 52)])

    preparation = prepare_semantic_submission(profile, tmp_path)

    assert len(preparation.eligible_requirement_ids) == 51
    assert preparation.reason_code == "SEMANTIC_INPUT_TOO_LARGE"
    assert preparation.call_ai is False
