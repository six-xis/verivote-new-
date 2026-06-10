import json
from typing import Any

import pytest
from httpx import AsyncClient

from app.crypto.commitment_v2 import compute_commitment_v2
from app.crypto.merkle import EMPTY_ROOT
from app.crypto.sealed_vote import compute_sealed_vote_package_hash, seal_vote_opening


DEMO_TALLY_KEY = "phase4-eligibility-demo-key"


async def create_election(client: AsyncClient, title: str = "Eligibility election") -> str:
    response = await client.post(
        "/api/v2/elections",
        json={"title": title, "description": "phase4 eligibility"},
    )
    assert response.status_code == 201
    return response.json()["election"]["id"]


async def add_candidates(client: AsyncClient, election_id: str, count: int = 4) -> None:
    for index in range(count):
        response = await client.post(
            f"/api/v2/elections/{election_id}/candidates",
            json={"name": f"Candidate {index + 1}", "description": "candidate"},
        )
        assert response.status_code == 201


async def bulletin_board(client: AsyncClient, election_id: str) -> dict[str, Any]:
    response = await client.get(f"/api/v2/elections/{election_id}/bulletin-board")
    assert response.status_code == 200
    return response.json()


async def issue_demo_credential(client: AsyncClient, election_id: str) -> dict[str, Any]:
    response = await client.post(f"/api/v2/elections/{election_id}/credentials/demo-issue")
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_demo_issue_updates_eligibility_root_and_public_credentials(
    client: AsyncClient,
) -> None:
    election_id = await create_election(client)
    initial_board = await bulletin_board(client, election_id)

    assert initial_board["manifest"]["eligibility_root"] == EMPTY_ROOT

    first_issue = await issue_demo_credential(client, election_id)
    assert first_issue["credential_id"]
    assert first_issue["credential_secret"]
    assert first_issue["credential_commitment"]
    assert first_issue["eligibility_root"]
    assert "demo only" in first_issue["warning"].lower()

    second_issue = await issue_demo_credential(client, election_id)
    assert second_issue["eligibility_root"] != first_issue["eligibility_root"]

    public_response = await client.get(f"/api/v2/elections/{election_id}/credentials/public")
    assert public_response.status_code == 200
    public_body = public_response.json()
    assert public_body["eligibility_root"] == second_issue["eligibility_root"]
    assert len(public_body["credentials"]) == 2
    assert public_body["credentials"][0]["credential_commitment"]
    assert public_body["credentials"][0]["eligibility_merkle_path"] is not None
    assert "credential_secret" not in json.dumps(public_body)

    board = await bulletin_board(client, election_id)
    assert board["manifest"]["eligibility_root"] == second_issue["eligibility_root"]
    assert "credential_secret" not in json.dumps(board)


@pytest.mark.asyncio
async def test_demo_nullifier_is_stable_per_election_and_changes_across_elections(
    client: AsyncClient,
) -> None:
    first_election_id = await create_election(client, "Eligibility election 1")
    second_election_id = await create_election(client, "Eligibility election 2")
    issue = await issue_demo_credential(client, first_election_id)
    secret = issue["credential_secret"]

    first_response = await client.post(
        f"/api/v2/elections/{first_election_id}/credentials/derive-nullifier",
        json={"credential_secret": secret},
    )
    repeat_response = await client.post(
        f"/api/v2/elections/{first_election_id}/credentials/derive-nullifier",
        json={"credential_secret": secret},
    )
    second_response = await client.post(
        f"/api/v2/elections/{second_election_id}/credentials/derive-nullifier",
        json={"credential_secret": secret},
    )

    assert first_response.status_code == 200
    assert repeat_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["nullifier_hash"] == repeat_response.json()["nullifier_hash"]
    assert first_response.json()["nullifier_hash"] != second_response.json()["nullifier_hash"]
    assert "demo" in first_response.json()["warning"].lower()
    assert "credential_secret" not in json.dumps(first_response.json())


@pytest.mark.asyncio
async def test_demo_nullifier_connects_to_abp_cast_without_leaking_secret(
    client: AsyncClient,
) -> None:
    election_id = await create_election(client)
    await add_candidates(client, election_id)
    issue = await issue_demo_credential(client, election_id)
    secret = issue["credential_secret"]
    board = await bulletin_board(client, election_id)
    election_id_hash = board["election_id_hash"]

    nullifier_response = await client.post(
        f"/api/v2/elections/{election_id}/credentials/derive-nullifier",
        json={"credential_secret": secret},
    )
    assert nullifier_response.status_code == 200
    nullifier_hash = nullifier_response.json()["nullifier_hash"]
    vote_vector = [1, 0, 0, 0]
    randomness = "phase4-cast-randomness"
    commitment = compute_commitment_v2(
        election_id_hash=election_id_hash,
        nullifier_hash=nullifier_hash,
        vote_vector=vote_vector,
        randomness=randomness,
    )
    sealed_vote_package = seal_vote_opening(
        {
            "vote_vector": vote_vector,
            "randomness": randomness,
            "candidate_count": len(vote_vector),
            "election_id_hash": election_id_hash,
            "nullifier_hash": nullifier_hash,
        },
        demo_key=DEMO_TALLY_KEY,
    )
    cast_payload = {
        "commitment": commitment,
        "nullifier_hash": nullifier_hash,
        "sealed_vote_package": sealed_vote_package,
        "sealed_vote_package_hash": compute_sealed_vote_package_hash(sealed_vote_package),
        "receipt_code": "phase4-receipt-code",
        "validity_proof_hash": "placeholder-proof-hash",
    }

    cast_response = await client.post(
        f"/api/v2/elections/{election_id}/ballots/cast",
        json=cast_payload,
    )
    assert cast_response.status_code == 201
    assert "credential_secret" not in json.dumps(cast_response.json())

    duplicate_response = await client.post(
        f"/api/v2/elections/{election_id}/ballots/cast",
        json=cast_payload,
    )
    assert duplicate_response.status_code == 409

    updated_board = await bulletin_board(client, election_id)
    assert updated_board["manifest"]["eligibility_root"] == issue["eligibility_root"]
    assert updated_board["cast_ballots_public"][0]["nullifier_hash"] == nullifier_hash
    assert "credential_secret" not in json.dumps(updated_board)
