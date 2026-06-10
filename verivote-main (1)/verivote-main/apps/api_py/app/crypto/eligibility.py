import secrets

from app.crypto.hash_utils import field_hash_v2
from app.crypto.merkle import (
    build_merkle_root,
    create_merkle_proof,
    verify_merkle_proof,
)


def generate_credential_secret() -> str:
    return secrets.token_hex(32)


def derive_credential_commitment(credential_secret: str) -> str:
    return field_hash_v2(
        "VERIVOTE_CREDENTIAL_COMMITMENT_V1",
        [credential_secret],
    )


def derive_nullifier_hash(election_id_hash: str, credential_secret: str) -> str:
    return field_hash_v2(
        "VERIVOTE_NULLIFIER_V1",
        [election_id_hash, credential_secret],
    )


def build_eligibility_root(credential_commitments: list[str]) -> str:
    return build_merkle_root(credential_commitments)


def create_eligibility_merkle_proof(
    credential_commitments: list[str],
    credential_commitment: str,
) -> list[dict[str, str]]:
    return create_merkle_proof(credential_commitments, credential_commitment)


def verify_eligibility_merkle_proof(
    credential_commitment: str,
    proof: list[dict],
    eligibility_root: str,
) -> bool:
    return verify_merkle_proof(credential_commitment, proof, eligibility_root)
