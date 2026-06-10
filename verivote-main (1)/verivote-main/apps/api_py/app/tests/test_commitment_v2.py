import pytest

from app.crypto.commitment_v2 import (
    VoteVectorValidationError,
    compute_commitment_v2,
    validate_vote_vector,
)


def test_commitment_v2_is_stable_for_same_input() -> None:
    first = compute_commitment_v2("election_hash", "nullifier_hash", [1, 0, 0, 0], "r")
    second = compute_commitment_v2("election_hash", "nullifier_hash", [1, 0, 0, 0], "r")

    assert first == second


def test_commitment_v2_changes_when_vote_vector_changes() -> None:
    assert compute_commitment_v2("e", "n", [1, 0, 0, 0], "r") != compute_commitment_v2(
        "e", "n", [0, 1, 0, 0], "r"
    )


def test_commitment_v2_changes_when_randomness_changes() -> None:
    assert compute_commitment_v2("e", "n", [1, 0, 0, 0], "r1") != compute_commitment_v2(
        "e", "n", [1, 0, 0, 0], "r2"
    )


def test_commitment_v2_changes_when_election_hash_changes() -> None:
    assert compute_commitment_v2("e1", "n", [1, 0, 0, 0], "r") != compute_commitment_v2(
        "e2", "n", [1, 0, 0, 0], "r"
    )


def test_commitment_v2_changes_when_nullifier_hash_changes() -> None:
    assert compute_commitment_v2("e", "n1", [1, 0, 0, 0], "r") != compute_commitment_v2(
        "e", "n2", [1, 0, 0, 0], "r"
    )


@pytest.mark.parametrize(
    "vote_vector",
    [
        [1, 1, 0, 0],
        [0, 0, 0, 0],
        [2, 0, 0, 0],
    ],
)
def test_commitment_v2_rejects_invalid_vote_vectors(vote_vector: list[int]) -> None:
    with pytest.raises(VoteVectorValidationError):
        compute_commitment_v2("e", "n", vote_vector, "r")


def test_validate_vote_vector_rejects_length_mismatch() -> None:
    with pytest.raises(VoteVectorValidationError):
        validate_vote_vector([1, 0, 0], candidate_count=4)

