"""Injectable provider boundary. The default is local heuristics, NOT an AI model."""
import re
from typing import Literal, Protocol
from app.models.profiles import AnnouncementSource, ExtractedRequirement, SourceEvidence


class RequirementExtractor(Protocol):
    name: str
    execution_kind: Literal["ACTUAL", "SIMULATED"]

    def extract(self, source: AnnouncementSource) -> list[ExtractedRequirement]: ...


def atomicity_issues(rule: str) -> list[str]:
    # Conservative syntactic gate, not a semantic proof. Never silently approve compounds.
    if re.search(r"이며|이고|하며|하고|그리고|또한|;|\n|\s및\s|[.!?]\s+\S", rule):
        return ["ATOMICITY_REVIEW: 독립 조건을 한 항목에 합쳤는지 확인하고 단일 조건으로 수정하세요."]
    return []


class LocalRuleExtractor:
    name = "local-rules-v1 (no AI model)"
    execution_kind: Literal["ACTUAL", "SIMULATED"] = "ACTUAL"
    subject = re.compile(r"제출|접수|파일|PDF|MP4|영상|페이지|신청서|동의서|서명|자격|참가|지원|마감|저작권|초상권|링크|URL", re.I)

    def extract(self, source: AnnouncementSource) -> list[ExtractedRequirement]:
        requirements: list[ExtractedRequirement] = []
        section = "공고 본문"
        # Each quote stays byte-for-byte equivalent to a source text substring.
        # Do not infer implicit obligations, numerical limits or deadlines.
        for line_number, line in enumerate(source.text.splitlines(), 1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#") or (len(stripped) < 40 and stripped.endswith(":")):
                section = stripped
                continue
            for fragment in re.split(r"(?<=[.!?])\s+|;\s*|(?:이며|하며)\s*", stripped):
                quote = fragment.strip()
                if not quote or not self.subject.search(quote):
                    continue
                if re.search(r"권장|추천|가급적", quote):
                    modality, severity = "SHOULD", "REVIEW"
                elif re.search(r"선택|가능|할 수 있", quote):
                    modality, severity = "MAY", "INFO"
                elif re.search(r"금지|불가|안 된다|안됩니다", quote):
                    modality, severity = "MUST_NOT", "REVIEW"
                elif re.search(r"필수|반드시|해야|하여야|이어야|여야", quote):
                    modality, severity = "MUST", "REVIEW"
                else:
                    modality, severity = "INFO", "INFO"
                verifier = "DETERMINISTIC" if re.search(r"파일|PDF|MP4|페이지|초|MB|해상도", quote, re.I) else "SEMANTIC"
                if re.search(r"마감|자격|저작권|초상권|접수처", quote):
                    verifier, severity = "EXTERNAL", "EXTERNAL"
                elif re.search(r"https?://|URL|링크", quote, re.I):
                    verifier = "URL_CHECK"
                condition = quote if re.search(r"경우|때|한해|대상", quote) else "always"
                requirements.append(ExtractedRequirement(
                    requirement_id=f"G{len(requirements) + 1:03}", rule=quote,
                    modality=modality, severity=severity, verifier=verifier, condition=condition,
                    evidence=SourceEvidence(source_section=f"{section} · 줄 {line_number}", quote=quote), confidence=0.5,
                ))
                if len(requirements) > 100:
                    raise ValueError("추출 후보가 100개를 초과했습니다. 공고 입력 범위를 줄여 주세요.")
        return requirements


def get_extractor() -> RequirementExtractor:
    return LocalRuleExtractor()
