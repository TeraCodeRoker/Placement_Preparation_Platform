"""Provider abstraction for code execution (Strategy pattern, §11.2).

Sync (Django worker model). Execution NEVER happens in-process — only in the
external provider's sandbox (§11.5).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel

from apps.integrations.execution.errors import SubmissionTooLargeError


class ExecutionResult(BaseModel):
    stdout: str = ""
    stderr: str = ""
    time_ms: float | None = None
    timed_out: bool = False
    status: str = ""


def enforce_source_size(source_code: str, max_bytes: int) -> None:
    if len(source_code.encode("utf-8")) > max_bytes:
        raise SubmissionTooLargeError()


class CodeExecutionProvider(ABC):
    name: str = "abstract"

    @abstractmethod
    def execute(
        self, language: str, source_code: str, stdin: str, timeout_s: float
    ) -> ExecutionResult:
        raise NotImplementedError
