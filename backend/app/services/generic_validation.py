"""Canonical profile handoff. No generic submission verifier is implemented yet."""
from dataclasses import dataclass
from pathlib import Path
from app.models.profiles import GenericRequirementProfile
from app.models.schemas import CheckSession, Evidence, Requirement, ValidationResult
from app.validators.v15_adapter import metadata


def canonical_requirements(profile: GenericRequirementProfile) -> list[Requirement]:
    profile = GenericRequirementProfile.model_validate(profile.model_dump())
    if profile.status != "CONFIRMED":
        raise ValueError("Human confirmation required")
    return [Requirement(id=r.requirement_id, title=r.rule, description=r.condition, verifier=r.verifier,
                        announcement_evidence=Evidence(source=profile.announcement.name,
                            locator=f"{r.evidence.source_section} · chars {r.evidence_start}:{r.evidence_end}", excerpt=r.evidence.quote))
            for r in profile.requirements]


@dataclass
class GenericRun:
    raw: dict
    results: list[ValidationResult]
    complete: bool = False
    engine_sha256: str | None = None


def validate(session: CheckSession, package: Path) -> GenericRun:
    if session.validation_profile != "generic" or session.generic_profile is None:
        raise ValueError("Generic confirmed profile required")
    profile = GenericRequirementProfile.model_validate(session.generic_profile.model_dump())
    canonical = canonical_requirements(profile)
    if canonical != session.requirements:
        raise ValueError("Canonical profile handoff mismatch")
    actual = sorted((f.name, f.size_bytes, f.sha256) for f in (metadata(p) for p in package.iterdir() if p.is_file()))
    expected = sorted((f.name, f.size_bytes, f.sha256) for f in session.files)
    if not expected or actual != expected:
        raise ValueError("Submission receipts do not match uploaded bytes")
    results = []
    for requirement, rule in zip(canonical, profile.requirements, strict=True):
        external = rule.verifier == "EXTERNAL" or rule.severity == "EXTERNAL"
        results.append(ValidationResult(id=f"{profile.profile_id}:{rule.requirement_id}", requirement_id=rule.requirement_id,
            status="EXTERNAL" if external else "REVIEW", title=rule.rule,
            explanation="외부에서 직접 확인해야 하는 요구사항입니다." if external else "UNSUPPORTED: 이 요구사항의 자동 제출파일 검증은 아직 구현되지 않았습니다.",
            action="확정한 공고 근거와 제출파일을 직접 대조하세요. 사용자 승인은 파일 조건 충족 판정이 아닙니다.",
            announcement_evidence=requirement.announcement_evidence, submission_evidence=None, source_mode="generic_review"))
    return GenericRun(raw={"profile": profile.model_dump(mode="json"), "verification": "UNSUPPORTED",
                           "files": [f.model_dump() for f in session.files]}, results=results)
