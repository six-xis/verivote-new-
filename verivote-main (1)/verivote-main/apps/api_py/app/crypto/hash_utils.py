import hashlib
import secrets
from typing import Any

from app.crypto.canonical_json import canonical_json_dumps, canonical_json_bytes


BN254_FIELD_MODULUS = (
    21888242871839275222246405745257275088548364400416034343698204186575808495617
)


def canonical_json(value: Any) -> str:
    return canonical_json_dumps(value)


def sha256_hex(data: bytes | str) -> str:
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(raw).hexdigest()


def hash_json(data: Any) -> str:
    return sha256_hex(canonical_json_bytes(data))


def field_hash_v2(domain: str, values: list[Any]) -> str:
    """Reference SHA256-to-BN254-field hash.

    This is a Python reference/demo hash for backend tests and audit data flow.
    Future Circom circuits should replace or align it with a Poseidon-based
    implementation before this is described as production ZK commitment logic.
    """

    digest = hashlib.sha256(
        canonical_json_bytes(
            {
                "domain": domain,
                "hash": "sha256-to-bn254-reference",
                "values": values,
                "version": "verivote-field-hash-v2",
            }
        )
    ).digest()
    return str(int.from_bytes(digest, byteorder="big") % BN254_FIELD_MODULUS)


def random_field_element() -> str:
    return str(secrets.randbelow(BN254_FIELD_MODULUS))


def hash_object(domain: str, value: Any) -> str:
    return hash_json({"domain": domain, "value": value})

