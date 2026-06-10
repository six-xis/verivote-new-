from app.crypto.hash_utils import field_hash_v2


class VoteVectorValidationError(ValueError):
    pass


def validate_vote_vector(vote_vector: list[int], candidate_count: int) -> None:
    if len(vote_vector) != candidate_count:
        raise VoteVectorValidationError(
            f"vote_vector length must equal candidate_count: "
            f"{len(vote_vector)} != {candidate_count}"
        )

    invalid_values = [item for item in vote_vector if item not in (0, 1)]
    if invalid_values:
        raise VoteVectorValidationError("vote_vector entries must be 0 or 1")

    total = sum(vote_vector)
    if total > 1:
        raise VoteVectorValidationError("vote_vector is an overvote: sum must be 1")
    if total < 1:
        raise VoteVectorValidationError("vote_vector is an undervote: sum must be 1")


def compute_commitment_v2(
    election_id_hash: str,
    nullifier_hash: str,
    vote_vector: list[int],
    randomness: str,
) -> str:
    validate_vote_vector(vote_vector, len(vote_vector))
    return field_hash_v2(
        "VERIVOTE_COMMITMENT_V2",
        [
            election_id_hash,
            nullifier_hash,
            *vote_vector,
            randomness,
        ],
    )

