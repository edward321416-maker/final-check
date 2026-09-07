"""Isolated ChatGPT-authenticated Codex CLI planner for TASK08 typed plans."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from app.models.verifier_plans import PlannerCandidate, PlannerProvenance
from app.services.ai_providers import DISABLED, ProviderExecutionError, _failure_category, codex_binary


PROMPT_ROOT = Path(__file__).resolve().parents[1] / "prompts" / "task08"
PROMPT_PATH = PROMPT_ROOT / "planner-v1.txt"
SCHEMA_PATH = PROMPT_ROOT / "planner.schema.json"
MODEL = "gpt-5.6-sol"
EFFORT = "high"


def prompt_sha256() -> str:
    return hashlib.sha256(PROMPT_PATH.read_bytes()).hexdigest()


class CodexCliVerificationPlanner:
    def __init__(self):
        self.model = os.environ.get("FINAL_CHECK_AI_MODEL", MODEL)
        self.effort = os.environ.get("FINAL_CHECK_AI_REASONING", EFFORT)
        self.timeout = int(os.environ.get("FINAL_CHECK_AI_TIMEOUT_SECONDS", "600"))
        self.provenance = PlannerProvenance(
            provider="OpenAI via ChatGPT-authenticated Codex CLI",
            model=self.model,
            prompt_version="task08-planner-v1",
            prompt_sha256=prompt_sha256(),
            execution_kind="ACTUAL",
        )

    def plan(self, payload: dict) -> list[PlannerCandidate]:
        cli = codex_binary()
        original_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        auth_source = original_home / "auth.json"
        if not auth_source.is_file():
            raise ProviderExecutionError("Existing Codex authentication is unavailable")
        with tempfile.TemporaryDirectory(prefix="final-check-t08-planner-") as temporary:
            isolated = Path(temporary)
            work = isolated / "input"
            home = isolated / "codex-home"
            work.mkdir()
            home.mkdir()
            auth = home / "auth.json"
            shutil.copyfile(auth_source, auth)
            schema = work / "schema.json"
            shutil.copyfile(SCHEMA_PATH, schema)
            output = work / "response.json"
            request = PROMPT_PATH.read_text(encoding="utf-8") + "\n\nINPUT_JSON:\n" + json.dumps(payload, ensure_ascii=False)
            env = {key: value for key, value in os.environ.items() if key.upper() in {
                "PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "APPDATA",
                "LOCALAPPDATA", "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMDATA",
            }}
            env.update(CODEX_HOME=str(home), USERPROFILE=str(isolated), HOME=str(isolated))
            args = [str(cli)]
            for value in (
                'approval_policy="never"', 'sandbox_mode="read-only"', 'web_search="disabled"',
                "project_doc_max_bytes=0", "skills.include_instructions=false", "skills.bundled.enabled=false",
                "mcp_servers={}", f'model="{self.model}"', f'model_reasoning_effort="{self.effort}"',
            ):
                args.extend(["-c", value])
            for feature in DISABLED:
                args.extend(["--disable", feature])
            try:
                result = subprocess.run(
                    args + ["exec", "--ignore-user-config", "--skip-git-repo-check", "--ephemeral",
                            "--color", "never", "--output-schema", str(schema),
                            "--output-last-message", str(output), "-"],
                    input=request,
                    cwd=work,
                    env=env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=self.timeout,
                )
                if result.returncode != 0:
                    raise ProviderExecutionError(
                        f"Codex TASK08 planner failed (exit={result.returncode}, category={_failure_category(result.stderr)})"
                    )
                raw = json.loads(output.read_text(encoding="utf-8"))
                return [PlannerCandidate.model_validate({
                    **item,
                    "planner_provenance": self.provenance.model_dump(),
                }) for item in raw["plans"]]
            except subprocess.TimeoutExpired as error:
                raise ProviderExecutionError(f"Codex TASK08 planner timed out after {self.timeout}s") from error
            except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                raise ProviderExecutionError(
                    f"Codex TASK08 planner returned no valid structured result ({type(error).__name__})"
                ) from error
            finally:
                auth.unlink(missing_ok=True)


def get_verification_planner() -> CodexCliVerificationPlanner:
    return CodexCliVerificationPlanner()
