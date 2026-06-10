"""Cryptographic helpers for the Python baseline."""

from app.crypto.commitment_v2 import compute_commitment_v2, validate_vote_vector
from app.crypto.eligibility import (
    build_eligibility_root,
    create_eligibility_merkle_proof,
    derive_credential_commitment,
    derive_nullifier_hash,
    generate_credential_secret,
    verify_eligibility_merkle_proof,
)
from app.crypto.hash_utils import field_hash_v2, hash_json, random_field_element, sha256_hex
from app.crypto.sealed_vote import (
    compute_sealed_vote_package_hash,
    compute_vote_opening_hash,
    open_sealed_vote_package,
    seal_vote_opening,
)

__all__ = [
    "build_eligibility_root",
    "compute_commitment_v2",
    "compute_sealed_vote_package_hash",
    "compute_vote_opening_hash",
    "create_eligibility_merkle_proof",
    "derive_credential_commitment",
    "derive_nullifier_hash",
    "field_hash_v2",
    "generate_credential_secret",
    "hash_json",
    "open_sealed_vote_package",
    "random_field_element",
    "seal_vote_opening",
    "sha256_hex",
    "validate_vote_vector",
    "verify_eligibility_merkle_proof",
]
