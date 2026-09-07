"""Generic verifier orchestration, isolated from the frozen v1.5 engine."""
import hashlib
from dataclasses import dataclass
from pathlib import Path

from app.models.profiles import GenericRequirementProfile
from app.models.schemas import CheckSession, Evidence, Requirement, ValidationResult
from app.services.generic_inspection import inspect_submission, run_checker
from app.services.verifier_engine import result_for


def canonical_requirements(profile: GenericRequirementProfile) -> list[Requirement]:
    profile = GenericRequirementProfile.model_validate(profile.model_dump())
    if profile.status != "CONFIRMED":
        raise ValueError("Human confirmation required")
    return [Requirement(
        id=item.requirement_id,
        title=item.rule,
        description=item.condition,
        verifier=item.verifier,
        announcement_evidence=Evidence(
            source=profile.announcement.name,
            locator=f"{item.evidence.source_section} · chars {item.evidence_start}:{item.evidence_end}",
            excerpt=item.evidence.quote,
        ),
    ) for item in profile.requirements]


@dataclass
class GenericRun:
    raw: dict
    results: list[ValidationResult]
    complete: bool = False
    engine_sha256: str | None = None


def engine_sha256() -> str:
    digest = hashlib.sha256()
    root = Path(__file__).resolve().parent
    for name in ("generic_inspection.py", "generic_policy.py", "verifier_engine.py"):
        digest.update((root / name).read_bytes())
    return digest.hexdigest()


def validate(session: CheckSession, package: Path) -> GenericRun:
    if session.validation_profile != "generic" or session.generic_profile is None:
        raise ValueError("Generic confirmed profile required")
    profile = GenericRequirementProfile.model_validate(session.generic_profile.model_dump())
    canonical = canonical_requirements(profile)
    if canonical != session.requirements:
        raise ValueError("Canonical profile handoff mismatch")
    actual_files = inspect_submission(package)
    actual = sorted((item.name, item.size_bytes, item.sha256) for item in actual_files)
    expected = sorted((item.name, item.size_bytes, item.sha256) for item in session.files)
    if not expected or actual != expected:
        raise ValueError("Submission receipts do not match uploaded bytes")

    plan_set = session.verification_plan
    valid_plan_set = plan_set is not None and plan_set.is_valid_for(profile)
    plans = {plan.requirement_id: plan for plan in plan_set.plans} if valid_plan_set else {}
    results: list[ValidationResult] = []
    outcomes: list[dict] = []
    for requirement in profile.requirements:
        plan = plans.get(requirement.requirement_id)
        outcome = run_checker(plan, package) if plan and plan.status == "VERIFIED" else None
        result = result_for(requirement, profile.announcement, plan, outcome)
        results.append(result)
        outcomes.append({
            "requirement_id": requirement.requirement_id,
            "plan_id": plan.plan_id if plan else None,
            "gate_status": plan.status if plan else "MISSING",
            "checker_outcome": outcome.status if outcome else None,
            "measured_fact": outcome.measured_fact if outcome else None,
        })
    mandatory_ids = {item.requirement_id for item in profile.requirements if item.modality in {"MUST", "MUST_NOT"}}
    by_id = {result.requirement_id: result for result in results}
    complete = bool(valid_plan_set) and all(
        by_id.get(requirement_id) is not None and by_id[requirement_id].status in {"PASS", "BLOCKER"}
        for requirement_id in mandatory_ids
    )
    return GenericRun(
        raw={
            "profile_binding": {
                "profile_id": profile.profile_id,
                "profile_version": profile.version,
                "announcement_sha256": profile.announcement.sha256,
                "announcement_text_sha256": profile.announcement.text_sha256,
            },
            "plan_set": plan_set.model_dump(mode="json") if valid_plan_set else None,
            "plan_set_valid": valid_plan_set,
            "outcomes": outcomes,
            "files": [item.model_dump() for item in actual_files],
        },
        results=results,
        complete=complete,
        engine_sha256=engine_sha256() if valid_plan_set else None,
    )
