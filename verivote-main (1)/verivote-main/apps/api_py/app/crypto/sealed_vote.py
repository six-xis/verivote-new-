import base64
import json
import secrets
from datetime import UTC, datetime
from typing import Any, Literal

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pydantic import ConfigDict, BaseModel

from app.crypto.canonical_json import canonical_json_bytes
from app.crypto.commitment_v2 import validate_vote_vector
from app.crypto.hash_utils import hash_json, sha256_hex


class VoteOpeningV2(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vote_vector: list[int]
    randomness: str
    candidate_count: int
    election_id_hash: str
    nullifier_hash: str


class SealedVotePackageV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal["sealed-vote-v1"] = "sealed-vote-v1"
    algorithm: str
    ciphertext: str
    nonce: str
    key_id: str
    opening_hash: str
    created_at: datetime


def _derive_demo_aes_key(demo_key: str) -> bytes:
    return bytes.fromhex(sha256_hex(demo_key))


def _b64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64_decode(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def _aad(package: SealedVotePackageV1) -> bytes:
    return canonical_json_bytes(
        {
            "algorithm": package.algorithm,
            "key_id": package.key_id,
            "opening_hash": package.opening_hash,
            "version": package.version,
        }
    )


def compute_vote_opening_hash(opening: VoteOpeningV2 | dict[str, Any]) -> str:
    parsed = opening if isinstance(opening, VoteOpeningV2) else VoteOpeningV2(**opening)
    validate_vote_vector(parsed.vote_vector, parsed.candidate_count)
    return hash_json(parsed)


def seal_vote_opening(
    opening: VoteOpeningV2 | dict[str, Any],
    demo_key: str,
    key_id: str = "demo",
) -> dict[str, Any]:
    """Encrypt a vote opening using demo AESGCM tally encryption.

    This is not the final production public-key tally encryption scheme.
    """

    parsed = opening if isinstance(opening, VoteOpeningV2) else VoteOpeningV2(**opening)
    validate_vote_vector(parsed.vote_vector, parsed.candidate_count)

    opening_hash = compute_vote_opening_hash(parsed)
    nonce = secrets.token_bytes(12)
    package_without_ciphertext = SealedVotePackageV1(
        algorithm="AESGCM-SHA256-DEMO",
        ciphertext="",
        nonce=_b64_encode(nonce),
        key_id=key_id,
        opening_hash=opening_hash,
        created_at=datetime.now(UTC),
    )
    aesgcm = AESGCM(_derive_demo_aes_key(demo_key))
    ciphertext = aesgcm.encrypt(
        nonce,
        canonical_json_bytes(parsed),
        _aad(package_without_ciphertext),
    )
    package = package_without_ciphertext.model_copy(update={"ciphertext": _b64_encode(ciphertext)})
    return package.model_dump(mode="json")


def open_sealed_vote_package(package: dict[str, Any], demo_key: str) -> dict[str, Any]:
    parsed = SealedVotePackageV1(**package)
    aesgcm = AESGCM(_derive_demo_aes_key(demo_key))
    try:
        plaintext = aesgcm.decrypt(
            _b64_decode(parsed.nonce),
            _b64_decode(parsed.ciphertext),
            _aad(parsed),
        )
    except InvalidTag:
        raise ValueError("failed to decrypt sealed vote package with demo key") from None

    opening_data = json.loads(plaintext.decode("utf-8"))
    opening = VoteOpeningV2(**opening_data)
    if compute_vote_opening_hash(opening) != parsed.opening_hash:
        raise ValueError("sealed vote opening hash mismatch")
    return opening.model_dump(mode="json")


def compute_sealed_vote_package_hash(package: dict[str, Any]) -> str:
    parsed = SealedVotePackageV1(**package)
    return hash_json(parsed)

