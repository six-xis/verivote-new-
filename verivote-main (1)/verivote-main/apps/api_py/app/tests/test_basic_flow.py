import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_basic_legacy_flow(client: AsyncClient) -> None:
    election_response = await client.post(
        "/api/v2/elections",
        json={"title": "Python baseline election", "description": "pytest flow"},
    )
    assert election_response.status_code == 201
    election = election_response.json()["election"]
    election_id = election["id"]

    candidate_response = await client.post(
        f"/api/v2/elections/{election_id}/candidates",
        json={"name": "Candidate A", "description": "baseline candidate"},
    )
    assert candidate_response.status_code == 201
    candidate_id = candidate_response.json()["candidate"]["id"]

    user_response = await client.post(
        f"/api/v2/elections/{election_id}/users/demo-register",
        json={"user_id": "demo-user-1"},
    )
    assert user_response.status_code == 201
    assert user_response.json()["credential"]["user_id"] == "demo-user-1"

    vote_response = await client.post(
        f"/api/v2/elections/{election_id}/ballots/legacy-cast",
        json={"user_id": "demo-user-1", "candidate_id": candidate_id},
    )
    assert vote_response.status_code == 201
    assert vote_response.json()["ballot_id"]
    assert vote_response.json()["ballot"]["privacy_mode"] == "legacy_simple"

    duplicate_response = await client.post(
        f"/api/v2/elections/{election_id}/ballots/legacy-cast",
        json={"user_id": "demo-user-1", "candidate_id": candidate_id},
    )
    assert duplicate_response.status_code == 409

    audit_response = await client.get(f"/api/v2/elections/{election_id}/audit/report")
    assert audit_response.status_code == 200
    report = audit_response.json()["report"]
    assert report["status"] == "passed"
    assert report["total_ballots"] == 1
    assert report["valid_ballots"] == 1
    assert report["duplicate_ballots"] == 0
    assert report["invalid_ballots"] == 0
    assert report["receipt_chain_verified"] is True
    assert report["commitment_openings_verified"] is True

