from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict

from app.crypto.canonical_json import canonical_json_dumps
from app.crypto.hash_utils import BN254_FIELD_MODULUS, field_hash_v2, hash_json


class SampleModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created_at: datetime
    name: str


def test_canonical_json_dumps_is_key_order_insensitive() -> None:
    left = {"b": 2, "a": 1}
    right = {"a": 1, "b": 2}

    assert canonical_json_dumps(left) == canonical_json_dumps(right)
    assert canonical_json_dumps(left) == '{"a":1,"b":2}'


def test_canonical_json_dumps_supports_datetime_and_pydantic_model() -> None:
    model = SampleModel(created_at=datetime(2026, 1, 1, tzinfo=UTC), name="demo")

    assert canonical_json_dumps(model) == (
        '{"created_at":"2026-01-01T00:00:00Z","name":"demo"}'
    )


def test_hash_json_is_stable_for_same_semantic_object() -> None:
    assert hash_json({"b": [2, 3], "a": 1}) == hash_json({"a": 1, "b": [2, 3]})


def test_hash_json_changes_when_field_changes() -> None:
    assert hash_json({"a": 1}) != hash_json({"a": 2})


def test_field_hash_v2_is_stable_for_same_input() -> None:
    assert field_hash_v2("DOMAIN", ["a", 1]) == field_hash_v2("DOMAIN", ["a", 1])


def test_field_hash_v2_changes_when_domain_changes() -> None:
    assert field_hash_v2("DOMAIN_A", ["a", 1]) != field_hash_v2("DOMAIN_B", ["a", 1])


def test_field_hash_v2_returns_valid_field_element() -> None:
    value = int(field_hash_v2("DOMAIN", ["a", 1]))

    assert 0 <= value < BN254_FIELD_MODULUS

