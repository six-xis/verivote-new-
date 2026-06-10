import pytest
from httpx import AsyncClient


async def create_fixture(client: AsyncClient, user_id: str = "demo-user-attack") -> tuple[str, str]:
    election_response = await client.post(
        "/api/v2/elections",
        json={"title": f"Attack fixture {user_id}", "description": "attack baseline"},
    )
    assert election_response.status_code == 201
    election_id = election_response.json()["election"]["id"]

    candidate_response = await client.post(
        f"/api/v2/elections/{election_id}/candidates",
        json={"name": "Candidate A", "description": ""},
    )
    assert candidate_response.status_code == 201
    candidate_id = candidate_response.json()["candidate"]["id"]

    register_response = await client.post(
        f"/api/v2/elections/{election_id}/users/demo-register",
        json={"user_id": user_id},
    )
    assert register_response.status_code == 201

    cast_response = await client.post(
        f"/api/v2/elections/{election_id}/ballots/legacy-cast",
        json={"user_id": user_id, "candidate_id": candidate_id},
    )
    assert cast_response.status_code == 201
    return election_id, candidate_id


@pytest.mark.asyncio
async def test_normal_audit_report_passes(client: AsyncClient) -> None:
    election_id, _candidate_id = await create_fixture(client, "normal-user")

    response = await client.get(f"/api/v2/elections/{election_id}/audit/report")
    assert response.status_code == 200
    report = response.json()["report"]
    assert report["status"] == "passed"
    assert report["receipt_chain_verified"] is True
    assert report["commitment_openings_verified"] is True


@pytest.mark.asyncio
async def test_tampered_commitment_is_detected(client: AsyncClient) -> None:
    election_id, _candidate_id = await create_fixture(client, "tamper-user")

    attack_response = await client.post(
        f"/api/v2/attacks/elections/{election_id}/tamper-commitment"
    )
    assert attack_response.status_code == 200

    response = await client.get(f"/api/v2/elections/{election_id}/audit/report")
    assert response.status_code == 200
    report = response.json()["report"]
    assert report["status"] == "failed"
    assert report["receipt_chain_verified"] is False
    assert report["commitment_openings_verified"] is False
    assert report["commitment_opening_failures"]


@pytest.mark.asyncio
async def test_injected_duplicate_vote_is_detected(client: AsyncClient) -> None:
    election_id, _candidate_id = await create_fixture(client, "duplicate-user")

    attack_response = await client.post(
        f"/api/v2/attacks/elections/{election_id}/inject-duplicate"
    )
    assert attack_response.status_code == 200

    response = await client.get(f"/api/v2/elections/{election_id}/audit/report")
    assert response.status_code == 200
    report = response.json()["report"]
    assert report["status"] == "failed"
    assert report["total_ballots"] == 2
    assert report["duplicate_ballots"] == 1
    assert report["valid_ballots"] == 1

