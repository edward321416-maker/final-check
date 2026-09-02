"""Boundary for the ORIGINAL frozen Python validator, added after the mock browser gate.

No v1.5 source or callable contract was provided. This intentionally has no
replacement algorithm, dynamic import, fabricated response, or mock fallback.
Wire the original engine here after source/provenance and native I/O are known.
"""
from dataclasses import dataclass
from pathlib import Path
from app.models.schemas import Requirement, ValidationResult


class ValidatorUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class ValidatorInput:
    """Provisional application input, NOT a claim about v1.5's native signature."""
    announcement: Path
    submissions: tuple[Path, ...]
    requirements: tuple[Requirement, ...]


class ValidatorV15Adapter:
    available = False
    reason = "Original frozen Validator v1.5 Python source and native entrypoint are not supplied."

    def require_available(self) -> None:
        raise ValidatorUnavailable(self.reason)

    def validate(self, package: ValidatorInput) -> list[ValidationResult]:
        self.require_available()
        raise ValidatorUnavailable(self.reason)


validator_v15 = ValidatorV15Adapter()
