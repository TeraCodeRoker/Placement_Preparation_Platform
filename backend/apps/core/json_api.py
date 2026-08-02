"""Helpers for plain-Django JSON views: Pydantic parse + JSON response.

Keeps the schema-validation discipline (§10.2) without DRF: request bodies are
parsed/validated with Pydantic, responses are serialized from Pydantic models
(or dicts/lists) to JSON.
"""
from __future__ import annotations

import json
from typing import Any, TypeVar

from django.http import HttpRequest, JsonResponse
from pydantic import BaseModel, ValidationError

from apps.core.exceptions import ValidationAppError

ModelT = TypeVar("ModelT", bound=BaseModel)


def parse_body(request: HttpRequest, model: type[ModelT]) -> ModelT:
    try:
        raw = request.body or b"{}"
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationAppError("Request body must be valid JSON.") from exc
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ValidationAppError(
            "Request validation failed.", details={"errors": exc.errors(include_url=False)}
        ) from exc


def _serialize(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    return value


def json_response(payload: Any, status: int = 200) -> JsonResponse:
    return JsonResponse(_serialize(payload), status=status, safe=False)
