import pytest

from app.crypto.sealed_vote import (
    compute_sealed_vote_package_hash,
    compute_vote_opening_hash,
    open_sealed_vote_package,
    seal_vote_opening,
)
from app.models.abp import CastBallotRecordV2


def sample_opening() -> dict:
    return {
        "vote_vector": [1, 0, 0, 0],
        "randomness": "opening-randomness",
        "candidate_count": 4,
        "election_id_hash": "election_hash",
        "nullifier_hash": "nullifier_hash",
    }


def test_seal_vote_opening_ciphertext_does_not_contain_plaintext_field_names() -> None:
    package = seal_vote_opening(sample_opening(), demo_key="demo-key")

    assert "vote_vector" not in package["ciphertext"]
    assert "randomness" not in package["ciphertext"]


def test_seal_vote_opening_ciphertext_does_not_contain_plaintext_values() -> None:
    package = seal_vote_opening(sample_opening(), demo_key="demo-key")

    assert "opening-randomness" not in package["ciphertext"]


def test_open_sealed_vote_package_with_correct_demo_key() -> None:
    opening = sample_opening()
    package = seal_vote_opening(opening, demo_key="demo-key")

    assert open_sealed_vote_package(package, demo_key="demo-key") == opening


def test_open_sealed_vote_package_with_wrong_demo_key_fails() -> None:
    package = seal_vote_opening(sample_opening(), demo_key="demo-key")

    with pytest.raises(ValueError):
        open_sealed_vote_package(package, demo_key="wrong-key")


def test_compute_vote_opening_hash_is_stable() -> None:
    assert compute_vote_opening_hash(sample_opening()) == compute_vote_opening_hash(sample_opening())


def test_compute_vote_opening_hash_changes_when_opening_changes() -> None:
    changed = sample_opening()
    changed["randomness"] = "changed-randomness"

    assert compute_vote_opening_hash(sample_opening()) != compute_vote_opening_hash(changed)


def test_compute_sealed_vote_package_hash_is_stable() -> None:
    package = seal_vote_opening(sample_opening(), demo_key="demo-key")

    assert compute_sealed_vote_package_hash(package) == compute_sealed_vote_package_hash(package)


def test_compute_sealed_vote_package_hash_changes_when_ciphertext_changes() -> None:
    package = seal_vote_opening(sample_opening(), demo_key="demo-key")
    changed = {**package, "ciphertext": package["ciphertext"][:-1] + "A"}

    assert compute_sealed_vote_package_hash(package) != compute_sealed_vote_package_hash(changed)


def test_sealed_package_does_not_include_demo_key() -> None:
    package = seal_vote_opening(sample_opening(), demo_key="demo-key")

    assert "demo_key" not in package
    assert "demo-key" not in str(package)


def test_cast_ballot_record_v2_with_sealed_package_still_hides_plaintext_vote_fields() -> None:
    package = seal_vote_opening(sample_opening(), demo_key="demo-key")
    sealed_hash = compute_sealed_vote_package_hash(package)
    record = CastBallotRecordV2(
        ballot_id="ballot_1",
        election_id_hash="election_hash",
        commitment="commitment_v2",
        nullifier_hash="nullifier_hash",
        sealed_vote_package=package,
        sealed_vote_package_hash=sealed_hash,
        validity_proof_hash=None,
        receipt_code="receipt_code",
        receipt_chain_hash="receipt_chain_hash",
        created_at="2026-01-01T00:00:00Z",
    )
    dumped = record.model_dump(mode="json")

    assert "candidate_id" not in dumped
    assert "vote_vector" not in dumped
    assert "randomness" not in dumped
    assert dumped["sealed_vote_package_hash"] == sealed_hash

