import hashlib
import importlib
import json
from pathlib import Path

import pytest

from app.models.profiles import AnnouncementSource, ExtractedRequirement
from app.services import profiles
from app.services.ai_providers import CodexCliJsonProvider, ProviderExecutionError
from app.services.semantic_submission import SemanticPage, SemanticPreparation


ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = ROOT / "backend/app/prompts/task10/semantic-review-v1.txt"
SCHEMA_PATH = ROOT / "backend/app/prompts/task10/semantic-review.schema.json"
PROMPT_SHA256 = "c242a7cdcc9d4a1feddba58ce9a02a8db488227fe8bf8cf8f050d152f0d469cf"


def semantic_provider_module():
    module = importlib.util.find_spec("app.services.semantic_provider")
    assert module is not None, "TASK10 semantic provider is not implemented"
    return importlib.import_module("app.services.semantic_provider")


def requirement(requirement_id: str, *, rule: str, quote: str):
    source_text = quote
    digest = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    source = AnnouncementSource(
        source_type="TEXT",
        name="announcement.txt",
        sha256=digest,
        text_sha256=digest,
        text=source_text,
        ingestion_status="READABLE",
    )
    extracted = ExtractedRequirement(
        requirement_id=requirement_id,
        rule=rule,
        modality="MUST",
        severity="REVIEW",
        verifier="SEMANTIC",
        condition="always",
        evidence={"source_section": "Submission contents", "quote": quote},
        confidence=1,
    )
    item = profiles.anchor(extracted, source)
    item.extraction_status = "CONFIRMED"
    item.authoritative = True
    return item


def preparation() -> SemanticPreparation:
    return SemanticPreparation(
        eligible_requirement_ids=("R01", "R02"),
        document_id="D01",
        actual_filename="private-client-name.pdf",
        file_sha256="f" * 64,
        coverage="FULL",
        pages=(
            SemanticPage(
                page_id="D01-P001",
                page_number=1,
                text="Our proposal describes measurable impact.",
                text_sha256="a" * 64,
            ),
            SemanticPage(
                page_id="D01-P002",
                page_number=2,
                text="The implementation schedule is included.",
                text_sha256="b" * 64,
            ),
        ),
        total_characters=83,
        call_ai=True,
        reason_code=None,
    )


class FakeRunner:
    model = "gpt-5.6-sol"

    def __init__(self, response: dict):
        self.response = response
        self.payload = None

    def run(self, payload: dict) -> dict:
        self.payload = payload
        return self.response


def valid_response() -> dict:
    return {
        "reviews": [
            {
                "requirement_id": "R01",
                "assessment": "RELATED_EVIDENCE_FOUND",
                "evidence_candidates": [{
                    "document_id": "D01",
                    "page_id": "D01-P001",
                    "quote": "measurable impact",
                }],
            },
            {
                "requirement_id": "R02",
                "assessment": "NO_CLEAR_EVIDENCE",
                "evidence_candidates": [],
            },
        ]
    }


def test_provider_sends_only_confirmed_requirements_and_opaque_page_text():
    module = semantic_provider_module()
    runner = FakeRunner(valid_response())
    reviewer = module.CodexCliSubmissionSemanticReviewer(runner=runner)
    requirements = [
        requirement("R01", rule="Explain measurable impact.", quote="공고문 기대효과 항목"),
        requirement("R02", rule="Include an implementation schedule.", quote="공고문 추진일정 항목"),
    ]

    response = reviewer.review(requirements, preparation())

    assert response.model_dump(mode="json") == valid_response()
    assert runner.payload == {
        "requirements": [
            {
                "requirement_id": "R01",
                "rule": "Explain measurable impact.",
                "modality": "MUST",
                "condition": "always",
                "announcement_evidence": {
                    "source_section": "Submission contents",
                    "quote": "공고문 기대효과 항목",
                },
            },
            {
                "requirement_id": "R02",
                "rule": "Include an implementation schedule.",
                "modality": "MUST",
                "condition": "always",
                "announcement_evidence": {
                    "source_section": "Submission contents",
                    "quote": "공고문 추진일정 항목",
                },
            },
        ],
        "submission": {
            "document_id": "D01",
            "pages": [
                {"page_id": "D01-P001", "text": "Our proposal describes measurable impact."},
                {"page_id": "D01-P002", "text": "The implementation schedule is included."},
            ],
        },
    }
    serialized = json.dumps(runner.payload)
    assert "private-client-name.pdf" not in serialized
    assert "file_sha256" not in serialized
    assert "page_number" not in serialized
    assert "text_sha256" not in serialized


@pytest.mark.parametrize(
    "response",
    [
        {"reviews": [valid_response()["reviews"][0]]},
        {"reviews": [valid_response()["reviews"][0], valid_response()["reviews"][0]]},
        {"reviews": [valid_response()["reviews"][0], {
            "requirement_id": "R99",
            "assessment": "NO_CLEAR_EVIDENCE",
            "evidence_candidates": [],
        }]},
    ],
    ids=["missing", "duplicate", "unknown"],
)
def test_provider_rejects_non_exact_requirement_cardinality(response):
    module = semantic_provider_module()
    reviewer = module.CodexCliSubmissionSemanticReviewer(runner=FakeRunner(response))
    requirements = [
        requirement("R01", rule="Explain impact.", quote="기대효과"),
        requirement("R02", rule="Include schedule.", quote="추진일정"),
    ]

    with pytest.raises(ProviderExecutionError, match="TASK10 semantic schema validation failed") as raised:
        reviewer.review(requirements, preparation())

    assert raised.value.category == "SCHEMA_REJECTED"


def test_provider_rejects_product_verdict_field():
    module = semantic_provider_module()
    response = valid_response()
    response["reviews"][0]["status"] = "PASS"
    reviewer = module.CodexCliSubmissionSemanticReviewer(runner=FakeRunner(response))
    requirements = [
        requirement("R01", rule="Explain impact.", quote="기대효과"),
        requirement("R02", rule="Include schedule.", quote="추진일정"),
    ]

    with pytest.raises(ProviderExecutionError, match="TASK10 semantic schema validation failed") as raised:
        reviewer.review(requirements, preparation())

    assert raised.value.category == "SCHEMA_REJECTED"


@pytest.mark.parametrize("response", [{}, valid_response()], ids=["reviews", "evidence-candidates"])
def test_provider_rejects_missing_required_schema_field(response):
    module = semantic_provider_module()
    if "reviews" in response:
        del response["reviews"][1]["evidence_candidates"]
    reviewer = module.CodexCliSubmissionSemanticReviewer(runner=FakeRunner(response))
    requirements = [
        requirement("R01", rule="Explain impact.", quote="기대효과"),
        requirement("R02", rule="Include schedule.", quote="추진일정"),
    ]

    with pytest.raises(ProviderExecutionError, match="TASK10 semantic schema validation failed") as raised:
        reviewer.review(requirements, preparation())

    assert raised.value.category == "SCHEMA_REJECTED"


def test_provider_provenance_and_explicit_task10_runner_paths_are_frozen():
    module = semantic_provider_module()
    reviewer = module.CodexCliSubmissionSemanticReviewer()

    assert reviewer.requires_background is True
    assert reviewer.provenance.prompt_version == "task10-semantic-review-v1"
    assert reviewer.provenance.execution_kind == "ACTUAL"
    assert reviewer.provenance.model == "gpt-5.6-sol"
    assert reviewer.runner.prompt_path == PROMPT_PATH
    assert reviewer.runner.schema_path == SCHEMA_PATH
    assert hashlib.sha256(PROMPT_PATH.read_bytes()).hexdigest() == PROMPT_SHA256


def test_task06_runner_defaults_remain_unchanged():
    assert CodexCliJsonProvider("stage1").prompt_path == ROOT / "backend/app/prompts/task06/stage1-v1.txt"
    assert CodexCliJsonProvider("stage1").schema_path == ROOT / "backend/app/prompts/task06/stage1.schema.json"
    assert CodexCliJsonProvider("stage2").prompt_path == ROOT / "backend/app/prompts/task06/stage2-v1.txt"
    assert CodexCliJsonProvider("stage2").schema_path == ROOT / "backend/app/prompts/task06/stage2.schema.json"


def test_task06_runner_paths_can_be_overridden_independently(tmp_path):
    prompt = tmp_path / "prompt.txt"
    schema = tmp_path / "schema.json"

    assert CodexCliJsonProvider("stage1", prompt_path=prompt).prompt_path == prompt
    assert CodexCliJsonProvider("stage2", schema_path=schema).schema_path == schema


def test_task10_output_schema_is_closed_and_bounded():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    item = schema["properties"]["reviews"]["items"]
    candidate = item["properties"]["evidence_candidates"]["items"]

    assert schema["required"] == ["reviews"] and schema["additionalProperties"] is False
    assert schema["properties"]["reviews"]["maxItems"] == 50
    assert item["required"] == ["requirement_id", "assessment", "evidence_candidates"]
    assert item["additionalProperties"] is False
    assert item["properties"]["assessment"]["enum"] == ["RELATED_EVIDENCE_FOUND", "NO_CLEAR_EVIDENCE"]
    assert item["properties"]["evidence_candidates"]["maxItems"] == 3
    assert candidate["required"] == ["document_id", "page_id", "quote"]
    assert candidate["additionalProperties"] is False
    assert candidate["properties"]["document_id"]["const"] == "D01"
    assert candidate["properties"]["page_id"]["pattern"] == "^D01-P[0-9]{3}$"
    assert candidate["properties"]["quote"]["minLength"] == 1
    assert candidate["properties"]["quote"]["maxLength"] == 2000


def test_unsupported_submission_provider_has_no_local_fallback(monkeypatch):
    module = semantic_provider_module()
    monkeypatch.setenv("FINAL_CHECK_AI_PROVIDER", "local-fallback")

    with pytest.raises(ProviderExecutionError, match="Unknown AI provider") as raised:
        module.get_submission_semantic_reviewer()

    assert raised.value.category == "CONFIGURATION_REJECTED"
