from copy import deepcopy
from typing import Any

import pytest
from httpx import AsyncClient

from app.crypto.commitment_v2 import compute_commitment_v2
from app.crypto.hash_utils import hash_object
from app.crypto.sealed_vote import (
    compute_sealed_vote_package_hash,
    seal_vote_opening,
)
from app.services.ballot_service import (
    RECEIPT_CHAIN_GENESIS_V2,
    create_abp_v2_receipt_chain_hash,
)


DEMO_TALLY_KEY = "phase3-test-demo-key"


def find_key(value: Any, key_name: str) -> bool:
    if isinstance(value, dict):
        return key_name in value or any(find_key(child, key_name) for child in value.values())
    if isinstance(value, list):
        return any(find_key(child, key_name) for child in value)
    return False


async def create_election_with_candidates(client: AsyncClient, candidate_count: int = 4) -> str:
    election_response = await client.post(
        "/api/v2/elections",
        json={"title": "ABP cast election", "description": "phase3"},
    )
    assert election_response.status_code == 201
    election_id = election_response.json()["election"]["id"]

    for index in range(candidate_count):
        candidate_response = await client.post(
            f"/api/v2/elections/{election_id}/candidates",
            json={"name": f"Candidate {index + 1}", "description": "ABP candidate"},
        )
        assert candidate_response.status_code == 201

    return election_id


async def get_election_id_hash(client: AsyncClient, election_id: str) -> str:
    board_response = await client.get(f"/api/v2/elections/{election_id}/bulletin-board")
    assert board_response.status_code == 200
    return board_response.json()["election_id_hash"]


def build_cast_payload(
    election_id_hash: str,
    nullifier_label: str = "nullifier-1",
    vote_vector: list[int] | None = None,
    randomness: str = "opening-randomness-1",
) -> dict[str, Any]:
    vector = [0, 1, 0, 0] if vote_vector is None else vote_vector
    nullifier_hash = hash_object(
        "test.nullifier.v2",
        {"election_id_hash": election_id_hash, "label": nullifier_label},
    )
    commitment = compute_commitment_v2(
        election_id_hash=election_id_hash,
        nullifier_hash=nullifier_hash,
        vote_vector=vector,
        randomness=randomness,
    )
    sealed_vote_package = seal_vote_opening(
        {
            "vote_vector": vector,
            "randomness": randomness,
            "candidate_count": len(vector),
            "election_id_hash": election_id_hash,
            "nullifier_hash": nullifier_hash,
        },
        demo_key=DEMO_TALLY_KEY,
    )
    return {
        "commitment": commitment,
        "nullifier_hash": nullifier_hash,
        "sealed_vote_package": sealed_vote_package,
        "sealed_vote_package_hash": compute_sealed_vote_package_hash(sealed_vote_package),
        "receipt_code": hash_object(
            "test.receipt.v2",
            {
                "election_id_hash": election_id_hash,
                "nullifier_hash": nullifier_hash,
                "commitment": commitment,
            },
        ),
        "validity_proof_hash": "placeholder-proof-hash",
    }


@pytest.mark.asyncio
async def test_abp_cast_ballot_success_does_not_leak_plaintext(client: AsyncClient) -> None:
    election_id = await create_election_with_candidates(client)
    election_id_hash = await get_election_id_hash(client, election_id)
    payload = build_cast_payload(election_id_hash)

    response = await client.post(
        f"/api/v2/elections/{election_id}/ballots/cast",
        json=payload,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "cast"
    assert body["commitment"] == payload["commitment"]
    assert body["nullifier_hash"] == payload["nullifier_hash"]
    assert body["sealed_vote_package_hash"] == payload["sealed_vote_package_hash"]
    assert body["receipt_chain_hash"]
    assert "sealed_vote_package" not in body
    assert not find_key(body, "candidate_id")
    assert not find_key(body, "vote_vector")
    assert not find_key(body, "randomness")


@pytest.mark.asyncio
@pytest.mark.parametrize("private_key", ["candidate_id", "vote_vector", "randomness"])
async def test_abp_cast_ballot_rejects_top_level_private_fields(
    client: AsyncClient,
    private_key: str,
) -> None:
    election_id = await create_election_with_candidates(client)
    election_id_hash = await get_election_id_hash(client, election_id)
    payload = build_cast_payload(election_id_hash)
    payload[private_key] = "forbidden"

    response = await client.post(
        f"/api/v2/elections/{election_id}/ballots/cast",
        json=payload,
    )

    assert response.status_code in {400, 422}


@pytest.mark.asyncio
@pytest.mark.parametrize("private_key", ["candidate_id", "vote_vector", "randomness"])
async def test_abp_cast_ballot_rejects_private_fields_inside_sealed_package(
    client: AsyncClient,
    private_key: str,
) -> None:
    election_id = await create_election_with_candidates(client)
    election_id_hash = await get_election_id_hash(client, election_id)
    payload = build_cast_payload(election_id_hash)
    payload["sealed_vote_package"][private_key] = "forbidden"

    response = await client.post(
        f"/api/v2/elections/{election_id}/ballots/cast",
        json=payload,
    )

    assert response.status_code in {400, 422}


@pytest.mark.asyncio
async def test_abp_cast_ballot_rejects_wrong_sealed_package_hash(
    client: AsyncClient,
) -> None:
    election_id = await create_election_with_candidates(client)
    election_id_hash = await get_election_id_hash(client, election_id)
    payload = build_cast_payload(election_id_hash)
    payload["sealed_vote_package_hash"] = "wrong-package-hash"

    response = await client.post(
        f"/api/v2/elections/{election_id}/ballots/cast",
        json=payload,
    )

    assert response.status_code in {400, 422}


@pytest.mark.asyncio
async def test_abp_cast_ballot_rejects_tampered_sealed_package_ciphertext(
    client: AsyncClient,
) -> None:
    election_id = await create_election_with_candidates(client)
    election_id_hash = await get_election_id_hash(client, election_id)
    payload = build_cast_payload(election_id_hash)
    payload["sealed_vote_package"] = deepcopy(payload["sealed_vote_package"])
    payload["sealed_vote_package"]["ciphertext"] = "tampered-ciphertext"

    response = await client.post(
        f"/api/v2/elections/{election_id}/ballots/cast",
        json=payload,
    )

    assert response.status_code in {400, 422}


@pytest.mark.asyncio
async def test_abp_cast_ballot_rejects_duplicate_nullifier_and_accepts_distinct_nullifier(
    client: AsyncClient,
) -> None:
    election_id = await create_election_with_candidates(client)
    election_id_hash = await get_election_id_hash(client, election_id)
    first_payload = build_cast_payload(election_id_hash, nullifier_label="nullifier-1")

    first_response = await client.post(
        f"/api/v2/elections/{election_id}/ballots/cast",
        json=first_payload,
    )
    assert first_response.status_code == 201

    duplicate_response = await client.post(
        f"/api/v2/elections/{election_id}/ballots/cast",
        json=first_payload,
    )
    assert duplicate_response.status_code == 409

    second_payload = build_cast_payload(
        election_id_hash,
        nullifier_label="nullifier-2",
        vote_vector=[1, 0, 0, 0],
        randomness="opening-randomness-2",
    )
    second_response = await client.post(
        f"/api/v2/elections/{election_id}/ballots/cast",
        json=second_payload,
    )
    assert second_response.status_code == 201
    assert second_response.json()["nullifier_hash"] != first_response.json()["nullifier_hash"]
    assert second_response.json()["receipt_chain_hash"] != first_response.json()["receipt_chain_hash"]


@pytest.mark.asyncio
async def test_bulletin_board_returns_only_public_cast_ballot_fields(
    client: AsyncClient,
) -> None:
    election_id = await create_election_with_candidates(client)
    election_id_hash = await get_election_id_hash(client, election_id)
    payload = build_cast_payload(election_id_hash)

    cast_response = await client.post(
        f"/api/v2/elections/{election_id}/ballots/cast",
        json=payload,
    )
    assert cast_response.status_code == 201

    board_response = await client.get(f"/api/v2/elections/{election_id}/bulletin-board")

    assert board_response.status_code == 200
    board = board_response.json()
    assert board["election_id"] == election_id
    assert board["election_id_hash"] == election_id_hash
    assert board["manifest"]["election_id"] == election_id
    assert board["challenge_records"] == []
    assert len(board["cast_ballots_public"]) == 1
    public_ballot = board["cast_ballots_public"][0]
    assert public_ballot["sealed_vote_package_hash"] == payload["sealed_vote_package_hash"]
    assert public_ballot["receipt_chain_hash"] == cast_response.json()["receipt_chain_hash"]
    assert "sealed_vote_package" not in public_ballot
    assert not find_key(public_ballot, "candidate_id")
    assert not find_key(public_ballot, "vote_vector")
    assert not find_key(public_ballot, "randomness")


def test_abp_v2_receipt_chain_hash_is_stable_and_input_bound() -> None:
    base = create_abp_v2_receipt_chain_hash(
        previous_receipt_chain_hash=RECEIPT_CHAIN_GENESIS_V2,
        election_id_hash="election-hash",
        ballot_id="ballot-1",
        commitment="commitment-1",
        receipt_code="receipt-1",
        status="cast",
    )

    assert base == create_abp_v2_receipt_chain_hash(
        previous_receipt_chain_hash=RECEIPT_CHAIN_GENESIS_V2,
        election_id_hash="election-hash",
        ballot_id="ballot-1",
        commitment="commitment-1",
        receipt_code="receipt-1",
        status="cast",
    )
    assert base != create_abp_v2_receipt_chain_hash(
        previous_receipt_chain_hash=RECEIPT_CHAIN_GENESIS_V2,
        election_id_hash="election-hash",
        ballot_id="ballot-1",
        commitment="commitment-2",
        receipt_code="receipt-1",
        status="cast",
    )
    assert base != create_abp_v2_receipt_chain_hash(
        previous_receipt_chain_hash=RECEIPT_CHAIN_GENESIS_V2,
        election_id_hash="election-hash",
        ballot_id="ballot-1",
        commitment="commitment-1",
        receipt_code="receipt-2",
        status="cast",
    )
    assert base != create_abp_v2_receipt_chain_hash(
        previous_receipt_chain_hash=RECEIPT_CHAIN_GENESIS_V2,
        election_id_hash="election-hash",
        ballot_id="ballot-1",
        commitment="commitment-1",
        receipt_code="receipt-1",
        status="challenged",
    )
