"""Fail when common live credential material is present in tracked files."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KEY_PATTERN = re.compile(r"\b" + "sk" + r"-(?!test-)[A-Za-z0-9_-]{20,}\b")
TOKEN_PATTERN = re.compile(r"(?i)railway[_ -]?token\s*[:=]\s*[A-Za-z0-9_-]{16,}")


def tracked_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, text=True, encoding="utf-8",
    )
    return [ROOT / line for line in output.splitlines() if line]


def main() -> int:
    findings: list[str] = []
    for path in tracked_files():
        relative = path.relative_to(ROOT).as_posix()
        if path.name.casefold() == "auth.json":
            findings.append(f"forbidden auth material: {relative}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if KEY_PATTERN.search(text):
            findings.append(f"possible API key: {relative}")
        if TOKEN_PATTERN.search(text):
            findings.append(f"possible Railway token: {relative}")
    if findings:
        print("\n".join(findings))
        return 1
    print("No common live credential material found in tracked files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
