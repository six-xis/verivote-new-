from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

import json


def _normalize_for_json(data: Any) -> Any:
    if isinstance(data, BaseModel):
        return _normalize_for_json(data.model_dump(mode="json"))
    if isinstance(data, datetime):
        return data.isoformat()
    if isinstance(data, date):
        return data.isoformat()
    if isinstance(data, dict):
        return {str(key): _normalize_for_json(value) for key, value in data.items()}
    if isinstance(data, list | tuple):
        return [_normalize_for_json(item) for item in data]
    return data


def canonical_json_dumps(data: Any) -> str:
    return json.dumps(
        _normalize_for_json(data),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_json_bytes(data: Any) -> bytes:
    return canonical_json_dumps(data).encode("utf-8")

