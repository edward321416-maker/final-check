"""Closed TASK08 verifier-plan DSL. Planner output is data, never executable code."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import PurePath
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


CheckerType = Literal[
    "FILE_PRESENCE", "FILE_COUNT", "FILE_NAME", "FILE_TYPE", "FILE_SIZE",
    "PDF_PAGE_COUNT", "VIDEO_METADATA",
]
GateStatus = Literal["VERIFIED", "REVIEW_ONLY", "EXTERNAL"]
Operator = Literal[
    "EQ", "LT", "LTE", "GT", "GTE",
    "EXACT_LITERAL", "PREFIX_LITERAL", "SUFFIX_LITERAL", "CONTAINS_LITERAL",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlannerProvenance(StrictModel):
    provider: str = Field(min_length=1, max_length=200)
    model: str = Field(min_length=1, max_length=100)
    prompt_version: str = Field(min_length=1, max_length=100)
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_kind: Literal["ACTUAL", "SIMULATED"]


class TargetSelector(StrictModel):
    kind: Literal["EXACT_NAME", "UNIQUE_EXTENSION", "ALL_BY_EXTENSION", "ALL_FILES"]
    value: str | None

    @model_validator(mode="after")
    def closed_target(self) -> "TargetSelector":
        if self.kind == "ALL_FILES":
            if self.value is not None:
                raise ValueError("ALL_FILES has no value")
            return self
        if not self.value or not self.value.strip():
            raise ValueError("Target value is required")
        if self.kind in {"UNIQUE_EXTENSION", "ALL_BY_EXTENSION"}:
            if self.value.casefold() not in {".pdf", ".mp4"}:
                raise ValueError("Only current MVP extensions are supported")
            self.value = self.value.casefold()
            return self
        if PurePath(self.value).name != self.value or any(token in self.value for token in ("/", "\\", "..")):
            raise ValueError("EXACT_NAME must be a safe literal basename")
        return self


class PlannerConstraint(StrictModel):
    field: Literal[
        "PRESENCE", "COUNT", "NAME", "TYPE", "SIZE", "PAGE_COUNT",
        "DURATION_SECONDS", "WIDTH", "HEIGHT", "ASPECT_RATIO", "CONTAINER",
    ]
    operator: Operator
    value: int | float | str
    unit: Literal["NONE", "COUNT", "BYTES", "MB", "MIB", "SECONDS", "PIXELS", "RATIO"]

    @model_validator(mode="after")
    def closed_constraint(self) -> "PlannerConstraint":
        if isinstance(self.value, bool):
            raise ValueError("Boolean values are not supported")
        numeric_ops = {"EQ", "LT", "LTE", "GT", "GTE"}
        literal_ops = {"EXACT_LITERAL", "PREFIX_LITERAL", "SUFFIX_LITERAL", "CONTAINS_LITERAL"}
        expected: dict[str, tuple[set[str], set[str], type | tuple[type, ...]]] = {
            "PRESENCE": ({"EQ"}, {"NONE"}, str),
            "COUNT": (numeric_ops, {"COUNT"}, int),
            "NAME": (literal_ops, {"NONE"}, str),
            "TYPE": ({"EQ"}, {"NONE"}, str),
            "SIZE": (numeric_ops, {"BYTES", "MB", "MIB"}, (int, float)),
            "PAGE_COUNT": (numeric_ops, {"COUNT"}, int),
            "DURATION_SECONDS": (numeric_ops, {"SECONDS"}, (int, float)),
            "WIDTH": (numeric_ops, {"PIXELS"}, int),
            "HEIGHT": (numeric_ops, {"PIXELS"}, int),
            "ASPECT_RATIO": (numeric_ops, {"RATIO"}, (int, float, str)),
            "CONTAINER": ({"EQ"}, {"NONE"}, str),
        }
        operators, units, value_type = expected[self.field]
        if self.operator not in operators or self.unit not in units or not isinstance(self.value, value_type):
            raise ValueError("Constraint field/operator/value/unit combination is outside the DSL")
        if self.field == "PRESENCE" and self.value not in {"PRESENT", "ABSENT"}:
            raise ValueError("Presence value must be PRESENT or ABSENT")
        if self.field == "TYPE" and str(self.value).upper() not in {"PDF", "MP4"}:
            raise ValueError("Only PDF and MP4 types are supported")
        if self.field in {"NAME", "TYPE", "CONTAINER"} and not str(self.value).strip():
            raise ValueError("Literal value must be nonblank")
        if isinstance(self.value, (int, float)) and self.value < 0:
            raise ValueError("Numeric constraints cannot be negative")
        return self


class ParameterProvenance(StrictModel):
    evidence_quote: str = Field(min_length=1, max_length=4000)
    evidence_start: int = Field(ge=0)
    evidence_end: int = Field(gt=0)
    source_substring: str = Field(min_length=1, max_length=500)
    normalized_value: int | float | str
    operator: Operator


class PlannerCandidate(StrictModel):
    requirement_id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,39}$")
    planner_disposition: Literal["CANDIDATE", "REVIEW_ONLY", "EXTERNAL"]
    checker_type: CheckerType
    target_selector: TargetSelector
    constraint: PlannerConstraint
    parameter_provenance: ParameterProvenance
    planner_reason: str = Field(min_length=1, max_length=1000)
    planner_provenance: PlannerProvenance

    @model_validator(mode="after")
    def checker_matches_constraint(self) -> "PlannerCandidate":
        fields: dict[str, set[str]] = {
            "FILE_PRESENCE": {"PRESENCE"},
            "FILE_COUNT": {"COUNT"},
            "FILE_NAME": {"NAME"},
            "FILE_TYPE": {"TYPE"},
            "FILE_SIZE": {"SIZE"},
            "PDF_PAGE_COUNT": {"PAGE_COUNT"},
            "VIDEO_METADATA": {"DURATION_SECONDS", "WIDTH", "HEIGHT", "ASPECT_RATIO", "CONTAINER"},
        }
        if self.constraint.field not in fields[self.checker_type]:
            raise ValueError("Checker type and constraint field do not match")
        if self.parameter_provenance.operator != self.constraint.operator:
            raise ValueError("Operator provenance must match the constraint")
        return self


class GatedVerificationPlan(PlannerCandidate):
    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    status: GateStatus
    gate_reasons: list[str] = Field(default_factory=list, max_length=30)


def confirmed_requirements_sha256(profile: Any) -> str:
    payload = [
        requirement.model_dump(
            mode="json",
            include={
                "requirement_id", "rule", "modality", "severity", "verifier", "condition",
                "evidence", "evidence_start", "evidence_end", "authoritative", "extraction_status",
            },
        )
        for requirement in profile.requirements
    ]
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class VerificationPlanSet(StrictModel):
    plan_set_id: str = Field(default_factory=lambda: str(uuid4()))
    profile_id: str
    profile_version: int = Field(ge=1)
    announcement_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    announcement_text_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    confirmed_requirements_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    planner_provenance: PlannerProvenance
    plan_schema_version: Literal["task08-verification-plan-v1"] = "task08-verification-plan-v1"
    created_at: datetime
    plans: list[GatedVerificationPlan] = Field(max_length=500)

    def is_valid_for(self, profile: Any) -> bool:
        return (
            self.profile_id == profile.profile_id
            and self.profile_version == profile.version
            and self.announcement_sha256 == profile.announcement.sha256
            and self.announcement_text_sha256 == profile.announcement.text_sha256
            and self.confirmed_requirements_sha256 == confirmed_requirements_sha256(profile)
        )
