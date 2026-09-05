"""Two-stage provider boundary for the local MVP. Provider output is never authoritative."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Literal, Protocol

from app.models.profiles import (
    AnnouncementSource,
    ExtractedRequirement,
    ProviderProvenance,
    SemanticReview,
)
from app.services.extractors import LocalRuleExtractor

PROMPT_ROOT = Path(__file__).resolve().parents[1] / "prompts" / "task06"
MODEL = "gpt-5.6-sol"
EFFORT = "high"
DISABLED = [
    "shell_tool", "unified_exec", "apps", "plugins", "remote_plugin", "memories",
    "external_agent_memory_import", "multi_agent", "multi_agent_v2", "browser_use",
    "browser_use_external", "computer_use", "in_app_browser", "image_generation",
    "view_image", "hooks", "shell_snapshot", "workspace_dependencies", "code_mode",
    "code_mode_host", "skill_search", "skill_mcp_dependency_install", "tool_suggest", "goals",
]


class ProviderExecutionError(RuntimeError):
    pass


def _failure_category(stderr: str) -> str:
    """Return a stable, non-sensitive provider failure category."""
    message = stderr.casefold()
    if any(token in message for token in ("not logged in", "login required", "authentication", "unauthorized", "401")):
        return "AUTH_UNAVAILABLE"
    if any(token in message for token in ("timed out", "timeout")):
        return "TIMEOUT"
    if any(token in message for token in ("connection", "network", "stream disconnected", "dns", "proxy")):
        return "TRANSPORT_UNAVAILABLE"
    if any(token in message for token in ("unknown feature", "invalid value", "configuration", "config")):
        return "CONFIGURATION_REJECTED"
    return "PROVIDER_EXIT"


class RequirementGenerator(Protocol):
    provenance: ProviderProvenance
    requires_background: bool

    def generate(self, source: AnnouncementSource) -> list[ExtractedRequirement]: ...


class SemanticRequirementReviewer(Protocol):
    provenance: ProviderProvenance
    requires_background: bool

    def review(self, source: AnnouncementSource, candidates: list[ExtractedRequirement]) -> list[SemanticReview]: ...


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def provenance(stage: Literal["stage1", "stage2"], execution_kind: Literal["ACTUAL", "SIMULATED"],
               provider: str, model: str | None = None) -> ProviderProvenance:
    prompt = PROMPT_ROOT / f"{stage}-v1.txt"
    return ProviderProvenance(provider=provider, model=model, prompt_version=f"task06-{stage}-v1",
                              prompt_sha256=file_sha(prompt), execution_kind=execution_kind)


def codex_binary() -> Path:
    appdata = Path(os.environ.get("APPDATA", ""))
    vendor = appdata / "npm/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe"
    found = str(vendor) if vendor.is_file() else shutil.which("codex.exe") or shutil.which("codex")
    if not found:
        raise ProviderExecutionError("Codex CLI is unavailable")
    return Path(found)


class CodexCliJsonProvider:
    def __init__(self, stage: Literal["stage1", "stage2"]):
        self.stage = stage
        self.prompt_path = PROMPT_ROOT / f"{stage}-v1.txt"
        self.schema_path = PROMPT_ROOT / f"{stage}.schema.json"
        self.model = os.environ.get("FINAL_CHECK_AI_MODEL", MODEL)
        self.effort = os.environ.get("FINAL_CHECK_AI_REASONING", EFFORT)
        self.timeout = int(os.environ.get("FINAL_CHECK_AI_TIMEOUT_SECONDS", "600"))

    def run(self, payload: dict) -> dict:
        cli = codex_binary()
        original_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        auth_source = original_home / "auth.json"
        if not auth_source.is_file():
            raise ProviderExecutionError("Existing Codex authentication is unavailable")
        with tempfile.TemporaryDirectory(prefix=f"final-check-t06-{self.stage}-") as temporary:
            isolated = Path(temporary)
            work = isolated / "input"
            home = isolated / "codex-home"
            work.mkdir()
            home.mkdir()
            auth = home / "auth.json"
            shutil.copyfile(auth_source, auth)
            prompt = self.prompt_path.read_text(encoding="utf-8")
            schema = work / "schema.json"
            shutil.copyfile(self.schema_path, schema)
            request = prompt + "\n\nINPUT_JSON:\n" + json.dumps(payload, ensure_ascii=False)
            output = work / "response.json"
            env = {key: value for key, value in os.environ.items() if key.upper() in {
                "PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "APPDATA",
                "LOCALAPPDATA", "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMDATA",
            }}
            env.update(CODEX_HOME=str(home), USERPROFILE=str(isolated), HOME=str(isolated))
            args = [str(cli)]
            settings = [
                'approval_policy="never"', 'sandbox_mode="read-only"', 'web_search="disabled"',
                "project_doc_max_bytes=0", "skills.include_instructions=false",
                "skills.bundled.enabled=false", "mcp_servers={}", f'model="{self.model}"',
                f'model_reasoning_effort="{self.effort}"',
            ]
            for value in settings:
                args.extend(["-c", value])
            for feature in DISABLED:
                args.extend(["--disable", feature])
            try:
                result = subprocess.run(
                    args + ["exec", "--ignore-user-config", "--skip-git-repo-check", "--ephemeral",
                            "--color", "never", "--output-schema", str(schema),
                            "--output-last-message", str(output), "-"],
                    input=request, cwd=work, env=env, capture_output=True, text=True, encoding="utf-8",
                    timeout=self.timeout,
                )
                if result.returncode != 0:
                    category = _failure_category(result.stderr)
                    raise ProviderExecutionError(
                        f"Codex {self.stage} failed (exit={result.returncode}, category={category})"
                    )
                if not output.is_file():
                    raise ProviderExecutionError(f"Codex {self.stage} returned no output file")
                return json.loads(output.read_text(encoding="utf-8"))
            except subprocess.TimeoutExpired as error:
                raise ProviderExecutionError(f"Codex {self.stage} timed out after {self.timeout}s") from error
            except (OSError, json.JSONDecodeError) as error:
                raise ProviderExecutionError(
                    f"Codex {self.stage} returned no valid structured result ({type(error).__name__})"
                ) from error
            finally:
                auth.unlink(missing_ok=True)


class CodexCliRequirementGenerator:
    requires_background = True

    def __init__(self):
        self.runner = CodexCliJsonProvider("stage1")
        self.provenance = provenance("stage1", "ACTUAL", "OpenAI via ChatGPT-authenticated Codex CLI", self.runner.model)

    def generate(self, source: AnnouncementSource) -> list[ExtractedRequirement]:
        payload = {"source": {"name": source.name, "sha256": source.sha256, "text_sha256": source.text_sha256},
                   "SOURCE_TEXT": source.text}
        raw = self.runner.run(payload)
        try:
            return [ExtractedRequirement.model_validate(item) for item in raw["requirements"]]
        except (KeyError, TypeError, ValueError) as error:
            raise ProviderExecutionError("Codex Stage 1 schema validation failed") from error


class CodexCliSemanticReviewer:
    requires_background = True

    def __init__(self):
        self.runner = CodexCliJsonProvider("stage2")
        self.provenance = provenance("stage2", "ACTUAL", "OpenAI via ChatGPT-authenticated Codex CLI", self.runner.model)

    def review(self, source: AnnouncementSource, candidates: list[ExtractedRequirement]) -> list[SemanticReview]:
        payload = {"source": {"name": source.name, "sha256": source.sha256, "text_sha256": source.text_sha256},
                   "SOURCE_TEXT": source.text,
                   "candidates": [candidate.model_dump(mode="json") for candidate in candidates]}
        raw = self.runner.run(payload)
        try:
            return [SemanticReview.model_validate({**item, "reviewer": self.provenance.model_dump()}) for item in raw["reviews"]]
        except (KeyError, TypeError, ValueError) as error:
            raise ProviderExecutionError("Codex Stage 2 schema validation failed") from error


class LocalFallbackRequirementGenerator:
    requires_background = False

    def __init__(self):
        self.extractor = LocalRuleExtractor()
        self.provenance = provenance("stage1", "ACTUAL", "Fallback suggestions — local-rules-v1", None)

    def generate(self, source: AnnouncementSource) -> list[ExtractedRequirement]:
        return self.extractor.extract(source)


class LocalFallbackSemanticReviewer:
    requires_background = False

    def __init__(self):
        self.provenance = provenance("stage2", "SIMULATED", "Fallback reviewer — human review required", None)

    def review(self, source: AnnouncementSource, candidates: list[ExtractedRequirement]) -> list[SemanticReview]:
        return [SemanticReview(requirement_id=item.requirement_id, decision="REVIEW",
                               reason="AI semantic review was not run; inspect the source directly.",
                               semantic_support=False, condition_preserved=False, modality_supported=False,
                               needs_more_context=True, reviewer=self.provenance) for item in candidates]


def get_generator() -> RequirementGenerator:
    if os.environ.get("FINAL_CHECK_AI_PROVIDER", "codex").lower() == "local-fallback":
        return LocalFallbackRequirementGenerator()
    return CodexCliRequirementGenerator()


def get_reviewer() -> SemanticRequirementReviewer:
    if os.environ.get("FINAL_CHECK_AI_PROVIDER", "codex").lower() == "local-fallback":
        return LocalFallbackSemanticReviewer()
    return CodexCliSemanticReviewer()


def provider_status() -> dict:
    try:
        cli = codex_binary()
        version = subprocess.check_output([str(cli), "--version"], text=True, timeout=10).strip()
        return {"mode": "actual-local-ai", "provider": "Codex CLI", "version": version,
                "model": os.environ.get("FINAL_CHECK_AI_MODEL", MODEL)}
    except Exception:
        return {"mode": "unavailable", "provider": "Codex CLI", "version": None,
                "model": os.environ.get("FINAL_CHECK_AI_MODEL", MODEL)}
