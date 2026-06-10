from copy import deepcopy

from app.crypto.eligibility import (
    build_eligibility_root,
    create_eligibility_merkle_proof,
    derive_credential_commitment,
    derive_nullifier_hash,
    generate_credential_secret,
    verify_eligibility_merkle_proof,
)
from app.crypto.hash_utils import BN254_FIELD_MODULUS
from app.crypto.merkle import EMPTY_ROOT


def test_generate_credential_secret_returns_distinct_values() -> None:
    assert generate_credential_secret() != generate_credential_secret()


def test_credential_commitment_is_stable_for_same_secret() -> None:
    secret = "credential-secret"

    assert derive_credential_commitment(secret) == derive_credential_commitment(secret)


def test_credential_commitment_changes_for_different_secret() -> None:
    assert derive_credential_commitment("secret-1") != derive_credential_commitment("secret-2")


def test_nullifier_hash_is_stable_for_same_secret_and_election() -> None:
    secret = "credential-secret"
    election_id_hash = "election-hash"

    assert derive_nullifier_hash(election_id_hash, secret) == derive_nullifier_hash(
        election_id_hash,
        secret,
    )


def test_nullifier_hash_changes_for_different_election() -> None:
    secret = "credential-secret"

    assert derive_nullifier_hash("election-hash-1", secret) != derive_nullifier_hash(
        "election-hash-2",
        secret,
    )


def test_nullifier_hash_is_valid_field_element() -> None:
    nullifier_hash = derive_nullifier_hash("election-hash", "credential-secret")

    assert 0 <= int(nullifier_hash) < BN254_FIELD_MODULUS


def test_eligibility_root_is_stable_for_same_leaves() -> None:
    leaves = [
        derive_credential_commitment("secret-1"),
        derive_credential_commitment("secret-2"),
        derive_credential_commitment("secret-3"),
    ]

    assert build_eligibility_root(leaves) == build_eligibility_root(list(leaves))


def test_eligibility_root_changes_when_commitment_changes() -> None:
    leaves = [
        derive_credential_commitment("secret-1"),
        derive_credential_commitment("secret-2"),
    ]
    changed = [
        derive_credential_commitment("secret-1"),
        derive_credential_commitment("secret-3"),
    ]

    assert build_eligibility_root(leaves) != build_eligibility_root(changed)


def test_eligibility_merkle_proof_verifies_member() -> None:
    leaves = [
        derive_credential_commitment("secret-1"),
        derive_credential_commitment("secret-2"),
        derive_credential_commitment("secret-3"),
    ]
    leaf = leaves[1]
    root = build_eligibility_root(leaves)
    proof = create_eligibility_merkle_proof(leaves, leaf)

    assert verify_eligibility_merkle_proof(leaf, proof, root)


def test_wrong_credential_commitment_fails_membership_proof() -> None:
    leaves = [
        derive_credential_commitment("secret-1"),
        derive_credential_commitment("secret-2"),
        derive_credential_commitment("secret-3"),
    ]
    proof = create_eligibility_merkle_proof(leaves, leaves[1])

    assert not verify_eligibility_merkle_proof(
        derive_credential_commitment("wrong-secret"),
        proof,
        build_eligibility_root(leaves),
    )


def test_tampered_merkle_proof_fails_verification() -> None:
    leaves = [
        derive_credential_commitment("secret-1"),
        derive_credential_commitment("secret-2"),
        derive_credential_commitment("secret-3"),
    ]
    proof = create_eligibility_merkle_proof(leaves, leaves[1])
    tampered_proof = deepcopy(proof)
    tampered_proof[0]["sibling"] = derive_credential_commitment("tampered-sibling")

    assert not verify_eligibility_merkle_proof(
        leaves[1],
        tampered_proof,
        build_eligibility_root(leaves),
    )


def test_empty_credential_list_root_is_stable() -> None:
    assert build_eligibility_root([]) == EMPTY_ROOT
    assert build_eligibility_root([]) == build_eligibility_root([])
