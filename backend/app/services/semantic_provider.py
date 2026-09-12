"""Closed Codex provider for TASK10 submission semantic review."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

from app.models.profiles import ProfileRequirement, ProviderProvenance
from app.models.semantic_review import SemanticAIResponse
from app.services.ai_providers import (
    CodexCliJsonProvider,
    ProviderExecutionError,
    file_sha,
)
from app.services.semantic_submission import SemanticPreparation


PROMPT_ROOT = Path(__file__).resolve().parents[1] / "prompts" / "task10"
PROMPT_PATH = PROMPT_ROOT / "semantic-review-v1.txt"
SCHEMA_PATH = PROMPT_ROOT / "semantic-review.schema.json"
PROMPT_VERSION = "task10-semantic-review-v1"


class SubmissionSemanticReviewer(Protocol):
    provenance: ProviderProvenance
    requires_background: bool

    def review(
        self,
        requirements: list[ProfileRequirement],
        preparation: SemanticPreparation,
    ) -> SemanticAIResponse: ...


class CodexCliSubmissionSemanticReviewer:
    requires_background = True

    def __init__(self, runner: CodexCliJsonProvider | None = None):
        self.runner = runner or CodexCliJsonProvider(
            "task10-semantic",
            prompt_path=PROMPT_PATH,
            schema_path=SCHEMA_PATH,
        )
        self.provenance = ProviderProvenance(
            provider="OpenAI via ChatGPT-authenticated Codex CLI",
            model=self.runner.model,
            prompt_version=PROMPT_VERSION,
            prompt_sha256=file_sha(PROMPT_PATH),
            execution_kind="ACTUAL",
        )

    def review(
        self,
        requirements: list[ProfileRequirement],
        preparation: SemanticPreparation,
    ) -> SemanticAIResponse:
        expected_ids = list(preparation.eligible_requirement_ids)
        supplied_ids = [item.requirement_id for item in requirements]
        if len(supplied_ids) != len(set(supplied_ids)) or supplied_ids != expected_ids:
            raise ProviderExecutionError(
                "TASK10 semantic schema validation failed",
                category="SCHEMA_REJECTED",
            )

        payload = {
            "requirements": [
                {
                    "requirement_id": item.requirement_id,
                    "rule": item.rule,
                    "modality": item.modality,
                    "condition": item.condition,
                    "announcement_evidence": {
                        "source_section": item.evidence.source_section,
                        "quote": item.evidence.quote,
                    },
                }
                for item in requirements
            ],
            "submission": {
                "document_id": "D01",
                "pages": [
                    {"page_id": page.page_id, "text": page.text}
                    for page in preparation.pages
                ],
            },
        }
        raw = self.runner.run(payload)
        try:
            reviews = raw["reviews"]
            required_fields = {"requirement_id", "assessment", "evidence_candidates"}
            if not isinstance(reviews, list) or any(
                not isinstance(item, dict) or set(item) != required_fields
                for item in reviews
            ):
                raise ValueError("Review items must contain exactly the schema fields")
            response = SemanticAIResponse.model_validate(raw)
            response_ids = [item.requirement_id for item in response.reviews]
            if len(response_ids) != len(set(response_ids)) or set(response_ids) != set(expected_ids):
                raise ValueError("Review IDs do not match eligible requirement IDs")
            return response
        except (KeyError, TypeError, ValueError) as error:
            raise ProviderExecutionError(
                "TASK10 semantic schema validation failed",
                category="SCHEMA_REJECTED",
            ) from error


def get_submission_semantic_reviewer() -> SubmissionSemanticReviewer:
    selected = os.environ.get("FINAL_CHECK_AI_PROVIDER", "codex").lower()
    if selected == "codex":
        return CodexCliSubmissionSemanticReviewer()
    raise ProviderExecutionError("Unknown AI provider", category="CONFIGURATION_REJECTED")
