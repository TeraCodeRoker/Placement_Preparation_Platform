"""Defensive extraction of JSON from a model response (§10.2)."""
from __future__ import annotations

import json
import re
from typing import Any

from apps.integrations.gemini.errors import GeminiMalformedResponseError

_FENCE = re.compile(r"```(?:json)?\s*|```")


def extract_json(raw: str) -> Any:
    text = _FENCE.sub("", raw).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start, end = text.find(open_ch), text.rfind(close_ch)
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise GeminiMalformedResponseError()
