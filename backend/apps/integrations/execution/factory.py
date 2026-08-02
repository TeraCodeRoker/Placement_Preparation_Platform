"""Execution-provider factory + singleton (config-selected Strategy)."""
from __future__ import annotations

from django.conf import settings

from apps.integrations.execution.base import CodeExecutionProvider
from apps.integrations.execution.judge0 import Judge0ExecutionProvider
from apps.integrations.execution.paiza import PaizaExecutionProvider
from apps.integrations.execution.piston import PistonExecutionProvider

_provider_singleton: CodeExecutionProvider | None = None


def build_execution_provider() -> CodeExecutionProvider:
    """Config-selected Strategy. Default is Paiza (free + keyless) — see ADR-020."""
    provider = settings.EXECUTION_PROVIDER
    if provider == "judge0":
        return Judge0ExecutionProvider(
            settings.JUDGE0_URL,
            settings.JUDGE0_API_KEY,
            settings.JUDGE0_HOST,
            settings.EXECUTION_MAX_SOURCE_BYTES,
        )
    if provider == "piston":
        return PistonExecutionProvider(
            settings.PISTON_URL, settings.PISTON_API_KEY, settings.EXECUTION_MAX_SOURCE_BYTES
        )
    return PaizaExecutionProvider(
        settings.PAIZA_URL, settings.PAIZA_API_KEY, settings.EXECUTION_MAX_SOURCE_BYTES
    )


def get_execution_provider() -> CodeExecutionProvider:
    global _provider_singleton
    if _provider_singleton is None:
        _provider_singleton = build_execution_provider()
    return _provider_singleton
