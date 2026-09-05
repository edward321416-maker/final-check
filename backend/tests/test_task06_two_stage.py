"""TASK 06 product-safety acceptance. Synthetic provider outputs are SIMULATED."""
import hashlib
from pathlib import Path

import pytest

from app.models.profiles import (ExtractedRequirement, ReviewRequest, SemanticReview,
                                 SourceEvidence)
from app.services import profiles
from app.services.ai_providers import provenance
from app.services.announcement_input import source_from_bytes
from app.validators.v15_adapter import EXPECTED_SHA256, FROZEN

ROOT = Path(__file__).resolve().parents[2]


def make_source(count: int):
    text = "\n".join(f"신청자는 제출파일 {index:03}을 PDF 형식으로 제출해야 한다." for index in range(1, count + 1))
    return source_from_bytes("synthetic-task06.txt", text.encode("utf-8"), "TEXT")


def make_candidates(source, count: int, severity: str = "REVIEW"):
    lines = source.text.splitlines()
    return [ExtractedRequirement(
        requirement_id=f"A{index:03}", rule=lines[index - 1], modality="MUST", severity=severity,
        verifier="DETERMINISTIC", condition="always",
        evidence=SourceEvidence(source_section=f"줄 {index}", quote=lines[index - 1]), confidence=0.7,
    ) for index in range(1, count + 1)]


class Generator:
    provenance = provenance("stage1", "SIMULATED", "task06-test-generator")

    def __init__(self, items):
        self.items = items

    def generate(self, source):
        return self.items


class Reviewer:
    provenance = provenance("stage2", "SIMULATED", "task06-test-reviewer")

    def __init__(self, decisions=None, fail_calls=None):
        self.decisions = decisions or {}
        self.fail_calls = set(fail_calls or [])
        self.calls = []

    def review(self, source, candidates):
        self.calls.append(len(candidates))
        if len(self.calls) in self.fail_calls:
            raise RuntimeError("test-only stage2 failure")
        output = []
        for item in candidates:
            decision, reason, duplicate_of = self.decisions.get(item.requirement_id, ("KEEP", "fully supported", None))
            supported = decision == "KEEP"
            output.append(SemanticReview(
                requirement_id=item.requirement_id, decision=decision, reason=reason,
                semantic_support=supported, condition_preserved=supported, modality_supported=supported,
                needs_more_context=decision == "REVIEW", duplicate_of=duplicate_of, reviewer=self.provenance,
            ))
        return output


def run(source, candidates, reviewer=None):
    return profiles.extract(profiles.new_profile(source), Generator(candidates), reviewer or Reviewer())


def test_t1_117_candidates_are_batched_without_all_or_nothing_loss():
    source = make_source(117)
    reviewer = Reviewer()
    result = run(source, make_candidates(source, 117), reviewer)
    assert result.raw_candidate_count == result.gated_candidate_count == len(result.requirements) == 117
    assert reviewer.calls == [50, 50, 17]
    assert result.overflow and result.pipeline_status == "OVERFLOW_REVIEW"
    assert result.extraction_complete and not result.failed_batches


def test_t2_evidence_mismatch_is_rejected_by_deterministic_gate():
    source = make_source(2)
    candidates = make_candidates(source, 2)
    candidates[0].evidence.quote = "원문에 없는 근거"
    result = run(source, candidates)
    assert result.raw_candidate_count == 2 and result.gated_candidate_count == 1
    assert [item.requirement_id for item in result.requirements] == ["A002"]
    assert any("evidence / offset" in notice for notice in result.notices)


def test_t3_unsupported_blocker_is_provisional_until_human_approval():
    source = make_source(1)
    reviewer = Reviewer({"A001": ("REVIEW", "quote does not support the full blocker", None)})
    result = run(source, make_candidates(source, 1, "BLOCKER"), reviewer)
    item = result.requirements[0]
    assert item.severity == "BLOCKER" and not item.authoritative
    assert item.extraction_status == "NEEDS_REVIEW" and item.stage2_decision == "REVIEW"
    with pytest.raises(ValueError, match="reviewed"):
        profiles.confirm(result)
    approved = profiles.review(result, "A001", ReviewRequest(expected_version=result.version, action="APPROVE"))
    assert approved.requirements[0].authoritative
    assert profiles.confirm(approved).status == "CONFIRMED"


@pytest.mark.parametrize(("quote", "reason"), [
    ("심사는 주최 측 심사위원이 진행한다.", "organizer operation"),
    ("총 상금은 1천만원이다.", "prize description"),
    ("성명", "empty form label"),
])
def test_t4_t5_organizer_prize_and_empty_form_labels_are_dropped(quote, reason):
    source = source_from_bytes("filter.txt", quote.encode("utf-8"), "TEXT")
    candidate = ExtractedRequirement(requirement_id="A001", rule=quote, modality="INFO", severity="INFO",
                                     verifier="SEMANTIC", condition="always",
                                     evidence=SourceEvidence(source_section="공고", quote=quote), confidence=0.5)
    result = run(source, [candidate], Reviewer({"A001": ("DROP", reason, None)}))
    assert result.requirements == [] and result.dropped_candidate_count == 1
    assert result.stage2_reviews[0].decision == "DROP"


def test_t6_duplicate_is_dropped_with_linked_provenance():
    text = "제안서는 PDF로 제출해야 한다.\n제안서는 PDF로 제출해야 한다."
    source = source_from_bytes("duplicate.txt", text.encode("utf-8"), "TEXT")
    candidates = [ExtractedRequirement(requirement_id=f"A00{index}", rule="제안서는 PDF로 제출해야 한다.",
                                       modality="MUST", severity="REVIEW", verifier="DETERMINISTIC",
                                       condition="always", evidence=SourceEvidence(source_section=f"줄 {index}", quote="제안서는 PDF로 제출해야 한다."), confidence=0.6)
                  for index in (1, 2)]
    reviewer = Reviewer({"A002": ("DROP", "duplicate obligation", "A001")})
    result = run(source, candidates, reviewer)
    assert [item.requirement_id for item in result.requirements] == ["A001"]
    dropped = next(review for review in result.stage2_reviews if review.requirement_id == "A002")
    assert dropped.duplicate_of == "A001"


def test_t7_condition_loss_is_held_for_review():
    source = make_source(1)
    result = run(source, make_candidates(source, 1), Reviewer({"A001": ("REVIEW", "condition was lost", None)}))
    item = result.requirements[0]
    assert item.extraction_status == "NEEDS_REVIEW" and not item.authoritative


def test_t8_provider_failure_cannot_activate_validation_or_ready_state():
    class BrokenGenerator(Generator):
        def generate(self, source):
            raise RuntimeError("test-only provider unavailable")

    source = make_source(1)
    result = profiles.extract(profiles.new_profile(source), BrokenGenerator([]), Reviewer())
    assert result.pipeline_status == "EXTRACTION_ERROR" and not result.extraction_complete
    assert result.requirements == [] and result.status == "REVIEW_REQUIRED"
    with pytest.raises(ValueError, match="reviewed"):
        profiles.confirm(result)


def test_t9_partial_stage2_failure_preserves_work_and_retries_only_failed_batch():
    source = make_source(160)
    failed_reviewer = Reviewer(fail_calls={4})
    partial = run(source, make_candidates(source, 160), failed_reviewer)
    assert len(partial.requirements) == 150 and partial.failed_batches == [3]
    assert not partial.extraction_complete and partial.pipeline_status == "REVIEW_REQUIRED"
    retry_reviewer = Reviewer()
    complete = profiles.extract(partial, Generator(partial.raw_candidates), retry_reviewer)
    assert retry_reviewer.calls == [10]
    assert len(complete.requirements) == 160 and not complete.failed_batches
    assert complete.extraction_complete and complete.pipeline_status == "OVERFLOW_REVIEW"


def test_hard_ceiling_is_explicit_and_never_silently_truncates():
    source = make_source(501)
    result = run(source, make_candidates(source, 501))
    assert result.raw_candidate_count == len(result.raw_candidates) == 501
    assert result.pipeline_status == "EXTRACTION_ERROR" and not result.extraction_complete
    assert any("HARD_CEILING_EXCEEDED" in notice for notice in result.notices)


def test_t10_frozen_validator_and_task04_gold_remain_unchanged():
    manifest = ROOT / "benchmarks/task04/gold_manifest.json"
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == "035ebc06d3d62db6ab9c47c53d30cbc206be02667d845e9db59da6b9c5f7fe89"
    assert hashlib.sha256(FROZEN.read_bytes()).hexdigest() == EXPECTED_SHA256 == "4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11"
