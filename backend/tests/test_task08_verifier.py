import hashlib
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError
from pypdf import PdfWriter
from fastapi.testclient import TestClient

from app.main import app
from app.models.profiles import AnnouncementSource, ExtractedRequirement, GenericRequirementProfile
from app.models.schemas import CheckSession, Evidence, Requirement, ValidationResult
from app.models.verifier_plans import (
    GatedVerificationPlan,
    ParameterProvenance,
    PlannerCandidate,
    PlannerConstraint,
    PlannerProvenance,
    TargetSelector,
)
from app.services import generic_inspection, generic_policy, generic_validation, profiles
from app.services import sessions
from app.services.ai_providers import ProviderExecutionError
from app.services.generic_inspection import CheckerOutcome, inspect_submission, run_checker
from app.services.storage import SQLiteRuntimeStore
from app.services.verifier_compiler import (
    compile_or_reuse,
    compile_profile,
    gate_candidate,
    planner_input,
)
from app.services.verifier_engine import result_for
from app.services.verifier_planner import get_verification_planner


MODEL = "gpt-5.6-sol"
PROMPT_SHA = "a" * 64
SCHEMA_VERSION = "task08-verification-plan-v1"


def source(text: str) -> AnnouncementSource:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return AnnouncementSource(
        source_type="TEXT",
        name="public-announcement.txt",
        sha256=digest,
        text_sha256=digest,
        text=text,
        ingestion_status="READABLE",
    )


def confirmed_profile(
    quote: str = "영상은 60초 이내여야 합니다.",
    *,
    rule: str = "영상 길이는 60초 이내여야 합니다.",
    modality: str = "MUST",
    severity: str = "BLOCKER",
    verifier: str = "DETERMINISTIC",
    condition: str = "always",
) -> GenericRequirementProfile:
    announcement = source(quote)
    extracted = ExtractedRequirement(
        requirement_id="G001",
        rule=rule,
        modality=modality,
        severity=severity,
        verifier=verifier,
        condition=condition,
        evidence={"source_section": "제출 규격", "quote": quote},
        confidence=1,
    )
    item = profiles.anchor(extracted, announcement)
    item.extraction_status = "CONFIRMED"
    item.authoritative = True
    profile = profiles.new_profile(announcement)
    profile.requirements = [item]
    profile.extraction_complete = True
    profile.status = "CONFIRMED"
    return GenericRequirementProfile.model_validate(profile.model_dump())


def provenance() -> PlannerProvenance:
    return PlannerProvenance(
        provider="OpenAI via ChatGPT-authenticated Codex CLI",
        model=MODEL,
        prompt_version="task08-planner-v1",
        prompt_sha256=PROMPT_SHA,
        execution_kind="SIMULATED",
    )


def candidate(
    profile: GenericRequirementProfile,
    *,
    checker_type: str = "VIDEO_METADATA",
    field: str = "DURATION_SECONDS",
    operator: str = "LTE",
    value=60,
    unit: str = "SECONDS",
    selector_kind: str = "UNIQUE_EXTENSION",
    selector_value: str | None = ".mp4",
    disposition: str = "CANDIDATE",
) -> PlannerCandidate:
    requirement = profile.requirements[0]
    return PlannerCandidate(
        requirement_id=requirement.requirement_id,
        planner_disposition=disposition,
        checker_type=checker_type,
        target_selector=TargetSelector(kind=selector_kind, value=selector_value),
        constraint=PlannerConstraint(field=field, operator=operator, value=value, unit=unit),
        parameter_provenance=ParameterProvenance(
            evidence_quote=requirement.evidence.quote,
            evidence_start=requirement.evidence_start,
            evidence_end=requirement.evidence_end,
            source_substring="60초 이내",
            normalized_value=value,
            operator=operator,
        ),
        planner_reason="공고의 명시적 영상 길이 상한입니다.",
        planner_provenance=provenance(),
    )


def verified_plan(profile: GenericRequirementProfile, **overrides) -> GatedVerificationPlan:
    gated = gate_candidate(profile, candidate(profile, **overrides))
    assert gated.status == "VERIFIED"
    return gated


class Planner:
    def __init__(self, outputs: list[PlannerCandidate]):
        self.outputs = outputs
        self.provenance = provenance()
        self.calls = 0
        self.payload = None

    def plan(self, payload: dict) -> list[PlannerCandidate]:
        self.calls += 1
        self.payload = payload
        return self.outputs


def write_pdf(path: Path, pages: int = 1) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=200, height=200)
    with path.open("wb") as stream:
        writer.write(stream)


def test_t1_only_confirmed_profile_can_compile():
    profile = confirmed_profile()
    profile.status = "REVIEW_REQUIRED"
    with pytest.raises(ValueError, match="confirmed"):
        compile_profile(profile, Planner([]))


def test_t2_planner_input_contains_no_submission_data():
    payload = planner_input(confirmed_profile())
    serialized = str(payload).casefold()
    assert "submission" not in serialized
    assert set(payload) == {"profile", "requirements"}


def test_t3_non_always_condition_is_review_only():
    profile = confirmed_profile(condition="수상작으로 선정된 경우")
    assert gate_candidate(profile, candidate(profile)).status == "REVIEW_ONLY"


@pytest.mark.parametrize("verifier", ["SEMANTIC", "VISION_SEMANTIC", "URL_CHECK", "EXTERNAL"])
def test_t4_unsupported_verifiers_are_not_executable(verifier):
    profile = confirmed_profile(verifier=verifier, severity="EXTERNAL" if verifier == "EXTERNAL" else "REVIEW")
    assert gate_candidate(profile, candidate(profile)).status in {"REVIEW_ONLY", "EXTERNAL"}


@pytest.mark.parametrize("modality", ["SHOULD", "MAY", "INFO"])
def test_t5_advisory_modalities_do_not_enter_blocking_lane(modality):
    profile = confirmed_profile(modality=modality, severity="REVIEW")
    assert gate_candidate(profile, candidate(profile)).status == "REVIEW_ONLY"


def test_t6_parameter_mismatch_is_review_only():
    profile = confirmed_profile("PDF는 10페이지 이내여야 합니다.", rule="PDF는 10페이지 이내")
    plan = candidate(profile, checker_type="PDF_PAGE_COUNT", field="PAGE_COUNT", value=20,
                     unit="COUNT", selector_kind="UNIQUE_EXTENSION", selector_value=".pdf")
    plan.parameter_provenance.source_substring = "10페이지"
    plan.parameter_provenance.normalized_value = 20
    assert gate_candidate(profile, plan).status == "REVIEW_ONLY"


def test_t7_operator_mismatch_is_review_only():
    profile = confirmed_profile("PDF는 10페이지 이내여야 합니다.", rule="PDF는 10페이지 이내")
    plan = candidate(profile, checker_type="PDF_PAGE_COUNT", field="PAGE_COUNT", operator="GTE", value=10,
                     unit="COUNT", selector_kind="UNIQUE_EXTENSION", selector_value=".pdf")
    plan.parameter_provenance.source_substring = "10페이지 이내"
    plan.parameter_provenance.operator = "GTE"
    assert gate_candidate(profile, plan).status == "REVIEW_ONLY"


def test_t7b_unit_mismatch_is_review_only():
    profile = confirmed_profile("영상 파일은 60MB 이내여야 합니다.", rule="영상 파일 60MB 이내")
    plan = candidate(profile, checker_type="VIDEO_METADATA", field="DURATION_SECONDS", operator="LTE", value=60,
                     unit="SECONDS", selector_kind="UNIQUE_EXTENSION", selector_value=".mp4")
    plan.parameter_provenance.source_substring = "60MB 이내"
    plan.parameter_provenance.normalized_value = 60
    assert gate_candidate(profile, plan).status == "REVIEW_ONLY"


@pytest.mark.parametrize("operator", ["EQ", "GT", "GTE"])
def test_t7_lte_phrase_cannot_be_reinterpreted_by_overlapping_markers(operator):
    profile = confirmed_profile("PDF는 10페이지 이내여야 합니다.", rule="PDF는 10페이지 이내")
    plan = candidate(profile, checker_type="PDF_PAGE_COUNT", field="PAGE_COUNT", operator=operator, value=10,
                     unit="COUNT", selector_kind="UNIQUE_EXTENSION", selector_value=".pdf")
    plan.parameter_provenance.source_substring = "10페이지 이내여야"
    plan.parameter_provenance.operator = operator
    plan.parameter_provenance.normalized_value = 10
    assert gate_candidate(profile, plan).status == "REVIEW_ONLY"


def test_t8_qualifier_loss_is_review_only():
    profile = confirmed_profile("표지를 제외하고 PDF는 10페이지 이내여야 합니다.", rule="표지 제외 10페이지 이내")
    plan = candidate(profile, checker_type="PDF_PAGE_COUNT", field="PAGE_COUNT", value=10,
                     unit="COUNT", selector_kind="UNIQUE_EXTENSION", selector_value=".pdf")
    plan.parameter_provenance.source_substring = "10페이지 이내"
    plan.parameter_provenance.normalized_value = 10
    assert gate_candidate(profile, plan).status == "REVIEW_ONLY"


@pytest.mark.parametrize("quote", [
    "본문만 PDF는 10페이지 이내여야 합니다.",
    "외부 데이터 사용 시 PDF는 10페이지 이내여야 합니다.",
])
def test_t8b_unsupported_qualifier_or_hidden_condition_is_review_only(quote):
    profile = confirmed_profile(quote, rule="PDF 10페이지 이내")
    plan = candidate(profile, checker_type="PDF_PAGE_COUNT", field="PAGE_COUNT", value=10,
                     unit="COUNT", selector_kind="UNIQUE_EXTENSION", selector_value=".pdf")
    plan.parameter_provenance.source_substring = "10페이지 이내"
    plan.parameter_provenance.normalized_value = 10
    assert gate_candidate(profile, plan).status == "REVIEW_ONLY"


def test_t9_ambiguous_target_returns_review(tmp_path):
    profile = confirmed_profile("PDF는 10페이지 이내여야 합니다.", rule="PDF는 10페이지 이내")
    plan = candidate(profile, checker_type="PDF_PAGE_COUNT", field="PAGE_COUNT", value=10,
                     unit="COUNT", selector_kind="UNIQUE_EXTENSION", selector_value=".pdf")
    plan.parameter_provenance.source_substring = "10페이지 이내"
    plan.parameter_provenance.normalized_value = 10
    gated = gate_candidate(profile, plan)
    write_pdf(tmp_path / "one.pdf")
    write_pdf(tmp_path / "two.pdf")
    assert run_checker(gated, tmp_path).status == "REVIEW"


@pytest.mark.parametrize("injection", [
    {"regex": ".*"}, {"shell": "dir"}, {"python": "pass"}, {"network": "https://example.com"},
    {"path": "C:/Windows"}, {"expression": "eval(1)"},
])
def test_t10_dsl_injection_is_schema_rejected(injection):
    data = candidate(confirmed_profile()).model_dump()
    data.update(injection)
    with pytest.raises(ValidationError):
        PlannerCandidate.model_validate(data)
    data = candidate(confirmed_profile()).model_dump()
    data["target_selector"] = {"kind": "EXACT_NAME", "value": "../secret.pdf"}
    with pytest.raises(ValidationError):
        PlannerCandidate.model_validate(data)


def test_t11_file_presence_pass_and_violation_have_evidence(tmp_path):
    profile = confirmed_profile("proposal.pdf 파일을 제출해야 합니다.", rule="proposal.pdf 제출")
    plan = candidate(profile, checker_type="FILE_PRESENCE", field="PRESENCE", operator="EQ", value="PRESENT",
                     unit="NONE", selector_kind="EXACT_NAME", selector_value="proposal.pdf")
    plan.parameter_provenance.source_substring = "proposal.pdf 파일을 제출"
    plan.parameter_provenance.normalized_value = "PRESENT"
    gated = gate_candidate(profile, plan)
    assert run_checker(gated, tmp_path).status == "VIOLATION"
    write_pdf(tmp_path / "proposal.pdf")
    outcome = run_checker(gated, tmp_path)
    assert outcome.status == "PASS" and outcome.submission_evidence


def test_t11b_extension_file_presence_pass_and_violation_have_evidence(tmp_path):
    profile = confirmed_profile("MP4 파일을 제출해야 합니다.", rule="MP4 파일 제출")
    plan = candidate(profile, checker_type="FILE_PRESENCE", field="PRESENCE", operator="EQ", value="PRESENT",
                     unit="NONE", selector_kind="ALL_BY_EXTENSION", selector_value=".mp4")
    plan.parameter_provenance.source_substring = "MP4 파일을 제출"
    plan.parameter_provenance.normalized_value = "PRESENT"
    gated = gate_candidate(profile, plan)
    assert gated.status == "VERIFIED"
    assert run_checker(gated, tmp_path).status == "VIOLATION"
    (tmp_path / "entry.mp4").write_bytes(b"not a video")
    outcome = run_checker(gated, tmp_path)
    assert outcome.status == "REVIEW" and outcome.submission_evidence
    fixture = Path(__file__).resolve().parents[2] / "fixtures/v15/demo-fixed/테스트어린이집_숏폼영상.MP4"
    (tmp_path / "entry.mp4").write_bytes(fixture.read_bytes())
    outcome = run_checker(gated, tmp_path)
    assert outcome.status == "PASS" and outcome.submission_evidence


def test_fake_mp4_presence_cannot_make_sole_mandatory_rule_ready(tmp_path):
    profile = confirmed_profile("MP4 파일을 제출해야 합니다.", rule="MP4 파일 제출")
    proposed = candidate(profile, checker_type="FILE_PRESENCE", field="PRESENCE", operator="EQ", value="PRESENT",
                         unit="NONE", selector_kind="ALL_BY_EXTENSION", selector_value=".mp4")
    proposed.parameter_provenance.source_substring = "MP4 파일을 제출"
    proposed.parameter_provenance.normalized_value = "PRESENT"
    plan_set = compile_profile(profile, Planner([proposed]))
    (tmp_path / "entry.mp4").write_bytes(b"not a video")
    session = CheckSession(
        id="fake-mp4-presence",
        created_at=profiles.now(),
        updated_at=profiles.now(),
        mode="custom",
        source_mode="generic_verifier",
        validation_profile="generic",
        generic_profile=profile,
        verification_plan=plan_set,
        verification_plan_state="READY",
        announcement_name=profile.announcement.name,
        requirements=generic_validation.canonical_requirements(profile),
        files=inspect_submission(tmp_path),
    )
    run = generic_validation.validate(session, tmp_path)
    assert run.results[0].status == "REVIEW"
    assert generic_policy.summarize(profile, run.results) == "REVIEW_REQUIRED"


def test_t12_file_count_pass_and_violation(tmp_path):
    profile = confirmed_profile("PDF 파일은 1개여야 합니다.", rule="PDF 1개 제출")
    plan = candidate(profile, checker_type="FILE_COUNT", field="COUNT", operator="EQ", value=1,
                     unit="COUNT", selector_kind="ALL_BY_EXTENSION", selector_value=".pdf")
    plan.parameter_provenance.source_substring = "1개여야"
    plan.parameter_provenance.normalized_value = 1
    gated = gate_candidate(profile, plan)
    assert run_checker(gated, tmp_path).status == "VIOLATION"
    write_pdf(tmp_path / "one.pdf")
    assert run_checker(gated, tmp_path).status == "PASS"


def test_t12b_total_file_count_all_files_is_grounded(tmp_path):
    profile = confirmed_profile("제출 파일은 총 2개여야 합니다.", rule="전체 파일 2개 제출")
    plan = candidate(profile, checker_type="FILE_COUNT", field="COUNT", operator="EQ", value=2,
                     unit="COUNT", selector_kind="ALL_FILES", selector_value=None)
    plan.parameter_provenance.source_substring = "총 2개여야"
    plan.parameter_provenance.normalized_value = 2
    gated = gate_candidate(profile, plan)
    assert gated.status == "VERIFIED"
    (tmp_path / "one.txt").write_text("one", encoding="utf-8")
    assert run_checker(gated, tmp_path).status == "VIOLATION"
    (tmp_path / "two.bin").write_bytes(b"two")
    assert run_checker(gated, tmp_path).status == "PASS"


def test_t12c_work_count_cannot_be_assumed_to_equal_file_count():
    profile = confirmed_profile("응모자별 작품은 최대 2개여야 합니다.", rule="작품 최대 2개")
    plan = candidate(profile, checker_type="FILE_COUNT", field="COUNT", operator="LTE", value=2,
                     unit="COUNT", selector_kind="ALL_FILES", selector_value=None)
    plan.parameter_provenance.source_substring = "작품은 최대 2개"
    plan.parameter_provenance.normalized_value = 2
    assert gate_candidate(profile, plan).status == "REVIEW_ONLY"


@pytest.mark.parametrize(("operator", "literal", "name"), [
    ("EXACT_LITERAL", "entry.pdf", "entry.pdf"),
    ("PREFIX_LITERAL", "entry", "entry-final.pdf"),
    ("SUFFIX_LITERAL", "-final.pdf", "entry-final.pdf"),
    ("CONTAINS_LITERAL", "final", "entry-final.pdf"),
])
def test_t13_file_name_literal_operators(tmp_path, operator, literal, name):
    profile = confirmed_profile(f"파일명은 {literal} 조건을 따라야 합니다.", rule="파일명 규칙")
    plan = candidate(profile, checker_type="FILE_NAME", field="NAME", operator=operator, value=literal,
                     unit="NONE", selector_kind="ALL_FILES", selector_value=None)
    plan.parameter_provenance.source_substring = literal
    plan.parameter_provenance.normalized_value = literal
    gated = gate_candidate(profile, plan)
    (tmp_path / name).write_bytes(b"x")
    assert run_checker(gated, tmp_path).status == "PASS"


def test_t13b_dynamic_filename_variables_are_review_only():
    literal = "팀명_작품명.pdf"
    profile = confirmed_profile(f"파일명은 {literal}여야 합니다.", rule="팀명과 작품명 파일명 규칙")
    plan = candidate(profile, checker_type="FILE_NAME", field="NAME", operator="EXACT_LITERAL", value=literal,
                     unit="NONE", selector_kind="ALL_FILES", selector_value=None)
    plan.parameter_provenance.source_substring = literal
    plan.parameter_provenance.normalized_value = literal
    assert gate_candidate(profile, plan).status == "REVIEW_ONLY"


def test_t14_extension_spoofing_cannot_pass_file_type(tmp_path):
    profile = confirmed_profile("제출 파일 형식은 PDF여야 합니다.", rule="PDF 형식")
    plan = candidate(profile, checker_type="FILE_TYPE", field="TYPE", operator="EQ", value="PDF",
                     unit="NONE", selector_kind="UNIQUE_EXTENSION", selector_value=".pdf")
    plan.parameter_provenance.source_substring = "PDF"
    plan.parameter_provenance.normalized_value = "PDF"
    gated = gate_candidate(profile, plan)
    (tmp_path / "fake.pdf").write_bytes(b"not a pdf")
    assert run_checker(gated, tmp_path).status != "PASS"


def test_t14a_file_type_mp4_ffprobe_unavailable_is_review(tmp_path, monkeypatch):
    profile = confirmed_profile("제출 파일 형식은 MP4여야 합니다.", rule="MP4 형식")
    plan = candidate(profile, checker_type="FILE_TYPE", field="TYPE", operator="EQ", value="MP4",
                     unit="NONE", selector_kind="UNIQUE_EXTENSION", selector_value=".mp4")
    plan.parameter_provenance.source_substring = "MP4"
    plan.parameter_provenance.normalized_value = "MP4"
    gated = gate_candidate(profile, plan)
    (tmp_path / "entry.mp4").write_bytes(b"untrusted bytes")
    monkeypatch.setattr(generic_inspection.shutil, "which", lambda _name: None)
    assert run_checker(gated, tmp_path).status == "REVIEW"


@pytest.mark.parametrize("error", [
    RuntimeError("FFPROBE_UNAVAILABLE"),
    subprocess.TimeoutExpired("ffprobe", 30),
    RuntimeError("FFPROBE_MALFORMED"),
    OSError("ffprobe execution failed"),
])
def test_t14b_file_type_mp4_probe_failure_is_review(tmp_path, monkeypatch, error):
    profile = confirmed_profile("제출 파일 형식은 MP4여야 합니다.", rule="MP4 형식")
    plan = candidate(profile, checker_type="FILE_TYPE", field="TYPE", operator="EQ", value="MP4",
                     unit="NONE", selector_kind="UNIQUE_EXTENSION", selector_value=".mp4")
    plan.parameter_provenance.source_substring = "MP4"
    plan.parameter_provenance.normalized_value = "MP4"
    gated = gate_candidate(profile, plan)
    (tmp_path / "entry.mp4").write_bytes(b"untrusted bytes")
    monkeypatch.setattr(generic_inspection, "_probe", lambda _path: (_ for _ in ()).throw(error))
    outcome = run_checker(gated, tmp_path)
    assert outcome.status == "REVIEW"
    result = result_for(profile.requirements[0], profile.announcement, gated, outcome)
    assert result.status == "REVIEW"
    assert generic_policy.summarize(profile, [result]) == "REVIEW_REQUIRED"


def test_t14c_file_type_mp4_confirmed_container_mismatch_is_violation(tmp_path, monkeypatch):
    profile = confirmed_profile("제출 파일 형식은 MP4여야 합니다.", rule="MP4 형식")
    plan = candidate(profile, checker_type="FILE_TYPE", field="TYPE", operator="EQ", value="MP4",
                     unit="NONE", selector_kind="UNIQUE_EXTENSION", selector_value=".mp4")
    plan.parameter_provenance.source_substring = "MP4"
    plan.parameter_provenance.normalized_value = "MP4"
    gated = gate_candidate(profile, plan)
    (tmp_path / "entry.mp4").write_bytes(b"container supplied by controlled probe")
    monkeypatch.setattr(generic_inspection, "_probe", lambda _path: {
        "stream": {"codec_type": "video"}, "format": {"format_name": "matroska,webm"},
    })
    assert run_checker(gated, tmp_path).status == "VIOLATION"


@pytest.mark.parametrize(("checker_type", "field", "operator", "value", "unit", "quote", "substring", "extension"), [
    ("FILE_COUNT", "COUNT", "EQ", 1, "COUNT", "PDF 파일은 1개여야 합니다.", "1개여야", ".pdf"),
    ("FILE_SIZE", "SIZE", "LTE", 1, "MB", "MP4 파일은 1MB 이하여야 합니다.", "1MB 이하", ".mp4"),
    ("FILE_NAME", "NAME", "EXACT_LITERAL", "entry.mp4", "NONE", "MP4 파일명은 entry.mp4여야 합니다.", "entry.mp4", ".mp4"),
])
def test_extension_target_checker_type_inspection_failure_cannot_pass(
    tmp_path, checker_type, field, operator, value, unit, quote, substring, extension,
):
    profile = confirmed_profile(quote, rule="확장자 대상 규칙")
    plan = candidate(profile, checker_type=checker_type, field=field, operator=operator, value=value,
                     unit=unit, selector_kind="ALL_BY_EXTENSION", selector_value=extension)
    plan.parameter_provenance.source_substring = substring
    plan.parameter_provenance.normalized_value = value
    gated = gate_candidate(profile, plan)
    name = str(value) if checker_type == "FILE_NAME" else f"fake{extension}"
    (tmp_path / name).write_bytes(b"not the declared media type")
    assert run_checker(gated, tmp_path).status == "REVIEW"


def test_t15_file_size_ambiguous_mb_boundary_is_review(tmp_path):
    profile = confirmed_profile("파일 크기는 1MB 이하여야 합니다.", rule="파일 크기 1MB 이하")
    plan = candidate(profile, checker_type="FILE_SIZE", field="SIZE", operator="LTE", value=1,
                     unit="MB", selector_kind="EXACT_NAME", selector_value="entry.pdf")
    plan.parameter_provenance.source_substring = "1MB 이하"
    plan.parameter_provenance.normalized_value = 1
    gated = gate_candidate(profile, plan)
    write_pdf(tmp_path / "entry.pdf")
    with (tmp_path / "entry.pdf").open("r+b") as stream:
        stream.truncate(1_020_000)
    assert run_checker(gated, tmp_path).status == "REVIEW"


def test_t16_pdf_page_count_and_parser_failure(tmp_path):
    profile = confirmed_profile("PDF는 2페이지 이내여야 합니다.", rule="PDF 2페이지 이내")
    plan = candidate(profile, checker_type="PDF_PAGE_COUNT", field="PAGE_COUNT", operator="LTE", value=2,
                     unit="COUNT", selector_kind="UNIQUE_EXTENSION", selector_value=".pdf")
    plan.parameter_provenance.source_substring = "2페이지 이내"
    plan.parameter_provenance.normalized_value = 2
    gated = gate_candidate(profile, plan)
    write_pdf(tmp_path / "valid.pdf", 2)
    assert run_checker(gated, tmp_path).status == "PASS"
    (tmp_path / "valid.pdf").write_bytes(b"broken")
    assert run_checker(gated, tmp_path).status == "REVIEW"


def test_t17_actual_ffprobe_metadata_and_failure(tmp_path):
    profile = confirmed_profile()
    plan = verified_plan(profile)
    fixture = Path(__file__).resolve().parents[2] / "fixtures/v15/demo-fixed/테스트어린이집_숏폼영상.MP4"
    (tmp_path / "entry.mp4").write_bytes(fixture.read_bytes())
    assert run_checker(plan, tmp_path).status == "PASS"
    (tmp_path / "entry.mp4").write_bytes(b"broken")
    assert run_checker(plan, tmp_path).status == "REVIEW"


@pytest.mark.parametrize(("quote", "field", "operator", "value", "unit", "substring"), [
    ("영상 너비는 1080px 이상이어야 합니다.", "WIDTH", "GTE", 1080, "PIXELS", "1080px 이상"),
    ("영상 높이는 1920px 이상이어야 합니다.", "HEIGHT", "GTE", 1920, "PIXELS", "1920px 이상"),
    ("영상 화면비는 9:16이어야 합니다.", "ASPECT_RATIO", "EQ", "9:16", "RATIO", "9:16이어야"),
    ("영상 형식은 MP4여야 합니다.", "CONTAINER", "EQ", "mp4", "NONE", "MP4"),
])
def test_t17_actual_ffprobe_supported_fields(tmp_path, quote, field, operator, value, unit, substring):
    profile = confirmed_profile(quote, rule=quote)
    plan = candidate(profile, field=field, operator=operator, value=value, unit=unit)
    plan.parameter_provenance.source_substring = substring
    plan.parameter_provenance.normalized_value = value
    gated = gate_candidate(profile, plan)
    assert gated.status == "VERIFIED"
    fixture = Path(__file__).resolve().parents[2] / "fixtures/v15/demo-fixed/테스트어린이집_숏폼영상.MP4"
    (tmp_path / "entry.mp4").write_bytes(fixture.read_bytes())
    assert run_checker(gated, tmp_path).status == "PASS"


def test_t18_unverified_plan_cannot_create_blocker():
    profile = confirmed_profile()
    plan = gate_candidate(profile, candidate(profile, disposition="REVIEW_ONLY"))
    outcome = CheckerOutcome(status="VIOLATION", measured_fact="duration=61", submission_evidence=Evidence(source="x.mp4", locator="ffprobe", excerpt="61"))
    assert result_for(profile.requirements[0], profile.announcement, plan, outcome).status == "REVIEW"


def test_t19_checker_failure_or_missing_evidence_cannot_create_pass():
    profile = confirmed_profile()
    plan = verified_plan(profile)
    outcome = CheckerOutcome(status="REVIEW", measured_fact="ffprobe unavailable", submission_evidence=None)
    assert result_for(profile.requirements[0], profile.announcement, plan, outcome).status == "REVIEW"


def test_t20_generic_review_lane_still_rejects_pass_and_blocker():
    with pytest.raises(ValidationError, match="Generic automatic"):
        ValidationResult(id="x", requirement_id="G001", status="PASS", title="x", explanation="x", action="x", source_mode="generic_review")


def test_t21_generic_verifier_verdict_requires_plan_and_submission_evidence():
    with pytest.raises(ValidationError):
        ValidationResult(id="x", requirement_id="G001", status="BLOCKER", title="x", explanation="x", action="x",
                         announcement_evidence=Evidence(source="a", locator="b", excerpt="c"),
                         submission_evidence=Evidence(source="d", locator="e", excerpt="f"), source_mode="generic_verifier")


def test_t22_generic_policy_blocks_only_authoritative_mandatory_blocker():
    profile = confirmed_profile()
    announcement = Evidence(source="a", locator="b", excerpt="c")
    submission = Evidence(source="d", locator="e", excerpt="f")
    blocker = ValidationResult(id="x", requirement_id="G001", status="BLOCKER", title="x", explanation="x", action="x",
                               announcement_evidence=announcement, submission_evidence=submission,
                               source_mode="generic_verifier", verification_plan_id="plan",
                               checker_type="VIDEO_METADATA", measured_fact="duration=61",
                               expected_constraint="duration <= 60")
    assert generic_policy.summarize(profile, [blocker]) == "BLOCKED"
    review = blocker.model_copy(update={"status": "REVIEW"})
    assert generic_policy.summarize(profile, [review]) == "REVIEW_REQUIRED"
    passed = blocker.model_copy(update={"status": "PASS"})
    assert generic_policy.summarize(profile, [passed]) == "READY"
    advisory = confirmed_profile(modality="SHOULD", severity="REVIEW")
    assert generic_policy.summarize(advisory, [review]) == "READY"
    nonblocking_severity = confirmed_profile(severity="REVIEW")
    assert generic_policy.summarize(nonblocking_severity, [blocker]) == "REVIEW_REQUIRED"


def test_t23_plan_set_survives_store_reconstruction(tmp_path):
    profile = confirmed_profile()
    plan_set = compile_profile(profile, Planner([candidate(profile)]))
    session = CheckSession(id="s", created_at=profiles.now(), updated_at=profiles.now(), mode="custom",
                           generic_profile=profile, verification_plan=plan_set)
    SQLiteRuntimeStore(tmp_path).save_session(session)
    restored = SQLiteRuntimeStore(tmp_path).get_session("s")
    assert restored.verification_plan == plan_set


def test_t24_changed_submission_reuses_same_plan_set():
    profile = confirmed_profile()
    planner = Planner([candidate(profile)])
    first = compile_or_reuse(profile, planner, None)
    second = compile_or_reuse(profile, planner, first)
    assert second.plan_set_id == first.plan_set_id and planner.calls == 1


def test_t25_profile_version_invalidates_old_plan_set():
    profile = confirmed_profile()
    plan_set = compile_profile(profile, Planner([candidate(profile)]))
    changed = profile.model_copy(deep=True)
    changed.version += 1
    assert not plan_set.is_valid_for(changed)


def test_t25_profile_identity_and_confirmed_contents_invalidate_old_plan_set():
    profile = confirmed_profile()
    plan_set = compile_profile(profile, Planner([candidate(profile)]))
    changed_id = profile.model_copy(deep=True)
    changed_id.profile_id = "different-profile"
    assert not plan_set.is_valid_for(changed_id)
    changed_rule = profile.model_copy(deep=True)
    changed_rule.requirements[0].rule = "변경된 확정 조건"
    assert not plan_set.is_valid_for(changed_rule)


def test_t26_source_hash_invalidates_old_plan_set():
    profile = confirmed_profile()
    plan_set = compile_profile(profile, Planner([candidate(profile)]))
    changed = profile.model_copy(deep=True)
    changed.announcement.sha256 = "b" * 64
    assert not plan_set.is_valid_for(changed)


def test_t27_frozen_validator_and_gold_manifest_are_unchanged():
    root = Path(__file__).resolve().parents[2]
    assert hashlib.sha256((root / "benchmarks/task04/gold_manifest.json").read_bytes()).hexdigest() == "035ebc06d3d62db6ab9c47c53d30cbc206be02667d845e9db59da6b9c5f7fe89"
    assert hashlib.sha256((root / "backend/app/validators/frozen_v15/validator_v1_5.py").read_bytes()).hexdigest() == "4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11"


def seeded_session(profile: GenericRequirementProfile) -> CheckSession:
    session = CheckSession(
        id="task08-session",
        created_at=profiles.now(),
        updated_at=profiles.now(),
        mode="custom",
        source_mode="generic_review",
        validation_profile="generic",
        generic_profile=profile,
        announcement_name=profile.announcement.name,
        requirements=generic_validation.canonical_requirements(profile),
    )
    return sessions.save(session)


def test_compile_api_failure_stays_in_explicit_review_path():
    profile = confirmed_profile()

    class FailingPlanner(Planner):
        def plan(self, payload):
            raise ProviderExecutionError("unavailable")

    app.dependency_overrides[get_verification_planner] = lambda: FailingPlanner([])
    try:
        with TestClient(app) as client:
            seeded_session(profile)
            response = client.post("/api/sessions/task08-session/verification-plan/compile", json={"expected_version": profile.version})
            assert response.status_code == 200
            body = response.json()
            assert body["verification_plan_state"] == "REVIEW_REQUIRED"
            assert body["verification_plan_error"] == "PLANNER_UNAVAILABLE"
            assert body["source_mode"] == "generic_review" and body["status"] is None
    finally:
        app.dependency_overrides.clear()


def test_actual_checker_api_broken_to_fixed_reuses_plan():
    profile = confirmed_profile()
    planner = Planner([candidate(profile)])
    app.dependency_overrides[get_verification_planner] = lambda: planner
    root = Path(__file__).resolve().parents[2]
    broken = root / "fixtures/v15/demo-broken/테스트어린이집_숏폼영상.MP4"
    fixed = root / "fixtures/v15/demo-fixed/테스트어린이집_숏폼영상.MP4"
    try:
        with TestClient(app) as client:
            seeded_session(profile)
            compiled = client.post("/api/sessions/task08-session/verification-plan/compile", json={"expected_version": profile.version})
            assert compiled.status_code == 200
            plan_set_id = compiled.json()["verification_plan"]["plan_set_id"]
            assert compiled.json()["source_mode"] == "generic_verifier"

            uploaded = client.post(
                "/api/sessions/task08-session/files",
                files=[("files", ("entry.mp4", broken.read_bytes(), "video/mp4"))],
            )
            assert uploaded.status_code == 200
            first = client.post("/api/sessions/task08-session/validate")
            assert first.status_code == 200 and first.json()["status"] == "BLOCKED"
            finding = first.json()["results"][0]
            assert finding["status"] == "BLOCKER"
            assert finding["announcement_evidence"] and finding["submission_evidence"]
            assert finding["verification_plan_id"] and finding["checker_type"] == "VIDEO_METADATA"

            uploaded = client.post(
                "/api/sessions/task08-session/files",
                files=[("files", ("entry.mp4", fixed.read_bytes(), "video/mp4"))],
            )
            assert uploaded.status_code == 200
            second = client.post("/api/sessions/task08-session/validate")
            assert second.status_code == 200 and second.json()["status"] == "READY"
            assert second.json()["results"][0]["status"] == "PASS"
            assert second.json()["verification_plan"]["plan_set_id"] == plan_set_id
            assert planner.calls == 1
    finally:
        app.dependency_overrides.clear()
