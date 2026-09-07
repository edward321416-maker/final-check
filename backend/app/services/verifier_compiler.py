"""Compile planner data through deterministic source grounding into executable plans."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Protocol

from app.models.profiles import GenericRequirementProfile, ProfileRequirement
from app.models.verifier_plans import (
    GatedVerificationPlan,
    PlannerCandidate,
    PlannerProvenance,
    VerificationPlanSet,
    confirmed_requirements_sha256,
)


class VerificationPlanner(Protocol):
    provenance: PlannerProvenance

    def plan(self, payload: dict) -> list[PlannerCandidate]: ...


def planner_input(profile: GenericRequirementProfile) -> dict:
    if profile.status != "CONFIRMED":
        raise ValueError("Human-confirmed profile required")
    return {
        "profile": {
            "profile_id": profile.profile_id,
            "profile_version": profile.version,
            "announcement": {
                "name": profile.announcement.name,
                "sha256": profile.announcement.sha256,
                "text_sha256": profile.announcement.text_sha256,
                "text": profile.announcement.text,
            },
        },
        "requirements": [
            {
                "requirement_id": item.requirement_id,
                "rule": item.rule,
                "modality": item.modality,
                "severity": item.severity,
                "verifier": item.verifier,
                "condition": item.condition,
                "authoritative": item.authoritative,
                "extraction_status": item.extraction_status,
                "evidence": {
                    "source_section": item.evidence.source_section,
                    "quote": item.evidence.quote,
                    "start": item.evidence_start,
                    "end": item.evidence_end,
                },
            }
            for item in profile.requirements
            if item.extraction_status == "CONFIRMED" and item.authoritative
        ],
    }


def _value_is_grounded(field: str, value: int | float | str, source: str) -> bool:
    compact = source.replace(",", "")
    if field == "PRESENCE":
        lowered = source.casefold()
        if value == "PRESENT":
            return any(marker in lowered for marker in ("제출", "포함", "첨부", "required", "include"))
        return any(marker in lowered for marker in ("금지", "제외", "제출하지", "must not", "exclude"))
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numbers = [float(token) for token in re.findall(r"(?<![\w.])\d+(?:\.\d+)?", compact)]
        return any(abs(number - float(value)) < 1e-9 for number in numbers)
    return str(value).casefold() in source.casefold()


def _operator_is_grounded(field: str, operator: str, source: str) -> bool:
    if field in {"PRESENCE", "NAME", "TYPE", "CONTAINER"}:
        return True
    lowered = source.casefold()
    ordered_meanings = (
        ("LTE", ("이내", "이하", "최대", "넘지", "초과하지", "at most", "no more than")),
        ("LT", ("미만", "less than")),
        ("GTE", ("이상", "최소", "at least", "no less than")),
        ("GT", ("초과", "more than")),
        ("EQ", ("정확히", "동일", "이어야", "여야", "exactly")),
    )
    inferred = next((meaning for meaning, markers in ordered_meanings if any(marker in lowered for marker in markers)), None)
    return inferred == operator


def _unit_is_grounded(unit: str, source: str) -> bool:
    lowered = source.casefold()
    markers: dict[str, tuple[str, ...]] = {
        "NONE": (),
        "COUNT": ("개", "건", "페이지", "page", "count"),
        "BYTES": ("byte", "바이트"),
        "MB": ("mb", "megabyte", "메가바이트"),
        "MIB": ("mib", "mebibyte", "메비바이트"),
        "SECONDS": ("초", "second", " sec"),
        "PIXELS": ("px", "픽셀", "해상도", "×"),
        "RATIO": ("비율", "ratio", ":"),
    }
    return unit == "NONE" or any(marker in lowered for marker in markers[unit])


def _target_is_grounded(checker_type: str, kind: str, value: str | None, quote: str) -> bool:
    lowered = quote.casefold()
    if kind == "ALL_FILES":
        return checker_type in {"FILE_COUNT", "FILE_NAME"} and any(
            marker in lowered for marker in ("파일", "첨부", "file")
        )
    assert value is not None
    if kind == "EXACT_NAME":
        return value.casefold() in lowered
    if value == ".mp4":
        return "mp4" in lowered or "영상" in lowered or "video" in lowered
    if value == ".pdf":
        return "pdf" in lowered
    return False


def _gate_reasons(requirement: ProfileRequirement, candidate: PlannerCandidate) -> list[str]:
    reasons: list[str] = []
    if requirement.extraction_status != "CONFIRMED" or not requirement.authoritative:
        reasons.append("REQUIREMENT_NOT_HUMAN_CONFIRMED")
    if requirement.verifier != "DETERMINISTIC":
        reasons.append("UNSUPPORTED_VERIFIER")
    if requirement.modality not in {"MUST", "MUST_NOT"}:
        reasons.append("NON_BLOCKING_MODALITY")
    if requirement.condition.strip().casefold() != "always":
        reasons.append("CONDITIONAL_REQUIREMENT")
    evidence = candidate.parameter_provenance
    if (
        evidence.evidence_quote != requirement.evidence.quote
        or evidence.evidence_start != requirement.evidence_start
        or evidence.evidence_end != requirement.evidence_end
        or requirement.evidence.quote[evidence.evidence_start - requirement.evidence_start:evidence.evidence_end - requirement.evidence_start]
        != evidence.evidence_quote
    ):
        reasons.append("EVIDENCE_MISMATCH")
    if evidence.source_substring not in requirement.evidence.quote:
        reasons.append("PARAMETER_SUBSTRING_MISSING")
    if evidence.normalized_value != candidate.constraint.value or not _value_is_grounded(
        candidate.constraint.field, candidate.constraint.value, evidence.source_substring
    ):
        reasons.append("PARAMETER_NOT_GROUNDED")
    if not _operator_is_grounded(candidate.constraint.field, candidate.constraint.operator, evidence.source_substring):
        reasons.append("OPERATOR_NOT_GROUNDED")
    if not _unit_is_grounded(candidate.constraint.unit, evidence.source_substring):
        reasons.append("UNIT_NOT_GROUNDED")
    if not _target_is_grounded(
        candidate.checker_type, candidate.target_selector.kind, candidate.target_selector.value,
        requirement.evidence.quote,
    ):
        reasons.append("TARGET_NOT_GROUNDED")
    qualifier_text = requirement.evidence.quote.casefold()
    qualifiers = (
        "표지 제외", "표지를 제외", "부록 제외", "부록을 제외", "목차 제외", "목차를 제외",
        "별첨 제외", "별첨을 제외", "본문만", "특정 서식", "선택한 섹션만",
        "excluding cover", "exclude cover", "excluding appendix", "exclude appendix",
    )
    if any(q in qualifier_text for q in qualifiers):
        reasons.append("QUALIFIER_LOSS")
    hidden_conditions = ("인 경우", "한 경우", "일 경우", "경우에", "경우에는", "최종심 진출자만", "외부 데이터 사용 시", "if ", "when ")
    if requirement.condition.strip().casefold() == "always" and any(marker in qualifier_text for marker in hidden_conditions):
        reasons.append("HIDDEN_CONDITIONAL")
    if candidate.checker_type == "FILE_NAME":
        name_value = str(candidate.constraint.value).casefold()
        dynamic_markers = ("팀명", "작품명", "성명", "이름", "접수번호", "<", ">", "{", "}")
        if any(marker in name_value for marker in dynamic_markers):
            reasons.append("DYNAMIC_FILENAME_UNSUPPORTED")
    return list(dict.fromkeys(reasons))


def gate_candidate(profile: GenericRequirementProfile, candidate: PlannerCandidate) -> GatedVerificationPlan:
    by_id = {item.requirement_id: item for item in profile.requirements}
    requirement = by_id.get(candidate.requirement_id)
    if requirement is None:
        raise ValueError("Planner returned an unknown requirement ID")
    reasons = _gate_reasons(requirement, candidate)
    if candidate.planner_disposition == "EXTERNAL" or requirement.verifier == "EXTERNAL" or requirement.severity == "EXTERNAL":
        status = "EXTERNAL"
    elif candidate.planner_disposition != "CANDIDATE" or reasons:
        status = "REVIEW_ONLY"
    else:
        status = "VERIFIED"
    return GatedVerificationPlan(**candidate.model_dump(), status=status, gate_reasons=reasons)


def compile_profile(profile: GenericRequirementProfile, planner: VerificationPlanner) -> VerificationPlanSet:
    payload = planner_input(profile)
    candidates = [PlannerCandidate.model_validate(item) for item in planner.plan(payload)]
    ids = [item.requirement_id for item in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("Planner returned duplicate requirement IDs")
    known = {item.requirement_id for item in profile.requirements if item.extraction_status == "CONFIRMED" and item.authoritative}
    if set(ids) != known:
        raise ValueError("Planner must return exactly one plan for every confirmed requirement")
    return VerificationPlanSet(
        profile_id=profile.profile_id,
        profile_version=profile.version,
        announcement_sha256=profile.announcement.sha256,
        announcement_text_sha256=profile.announcement.text_sha256,
        confirmed_requirements_sha256=confirmed_requirements_sha256(profile),
        planner_provenance=planner.provenance,
        created_at=datetime.now(timezone.utc),
        plans=[gate_candidate(profile, item) for item in candidates],
    )


def compile_or_reuse(
    profile: GenericRequirementProfile,
    planner: VerificationPlanner,
    existing: VerificationPlanSet | None,
) -> VerificationPlanSet:
    if existing is not None and existing.is_valid_for(profile):
        return existing
    return compile_profile(profile, planner)
