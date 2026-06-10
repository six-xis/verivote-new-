from typing import Any

import pytest
from httpx import AsyncClient


FORBIDDEN_PUBLIC_KEYS = {
    "candidate_id",
    "vote_vector",
    "randomness",
    "credential_secret",
    "sealed_vote_package",
}


def find_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    if isinstance(value, dict):
        findings: list[str] = []
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_PUBLIC_KEYS:
                findings.append(child_path)
            findings.extend(find_forbidden_keys(child, child_path))
        return findings
    if isinstance(value, list):
        findings = []
        for index, child in enumerate(value):
            findings.extend(find_forbidden_keys(child, f"{path}[{index}]"))
        return findings
    return []


@pytest.mark.asyncio
async def test_frontend_election_list_and_detail_are_public(client: AsyncClient) -> None:
    empty_response = await client.get("/api/v2/elections")
    assert empty_response.status_code == 200
    assert empty_response.json() == {"elections": []}

    election_response = await client.post(
        "/api/v2/elections",
        json={"title": "Frontend integration", "description": "Python API v2"},
    )
    assert election_response.status_code == 201
    election_id = election_response.json()["election"]["id"]

    candidate_response = await client.post(
        f"/api/v2/elections/{election_id}/candidates",
        json={"name": "Candidate A", "description": "Public candidate"},
    )
    assert candidate_response.status_code == 201

    list_response = await client.get("/api/v2/elections")
    assert list_response.status_code == 200
    listed = list_response.json()["elections"][0]
    assert listed["election_id"] == election_id
    assert listed["id"] == election_id
    assert listed["candidate_count"] == 1
    assert listed["election_id_hash"]
    assert find_forbidden_keys(listed) == []

    detail_response = await client.get(f"/api/v2/elections/{election_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()["election"]
    assert detail["id"] == election_id
    assert detail["candidates"][0]["id"] == candidate_response.json()["candidate"]["id"]
    assert find_forbidden_keys(detail) == []


@pytest.mark.asyncio
async def test_frontend_sanitized_vote_response_hides_plaintext_fields(
    client: AsyncClient,
) -> None:
    election_response = await client.post(
        "/api/v2/elections",
        json={"title": "Sanitized vote", "description": ""},
    )
    election_id = election_response.json()["election"]["id"]

    candidate_response = await client.post(
        f"/api/v2/elections/{election_id}/candidates",
        json={"name": "Candidate A", "description": ""},
    )
    candidate_id = candidate_response.json()["candidate"]["id"]

    register_response = await client.post(
        f"/api/v2/elections/{election_id}/users/demo-register",
        json={"user_id": "frontend-user"},
    )
    assert register_response.status_code == 201

    vote_response = await client.post(
        f"/api/v2/elections/{election_id}/vote",
        json={"user_id": "frontend-user", "candidate_id": candidate_id},
    )
    assert vote_response.status_code == 201
    payload = vote_response.json()
    assert payload["vote_id"]
    assert payload["receipt_code"]
    assert payload["receipt_chain_hash"]
    assert find_forbidden_keys(payload) == []


@pytest.mark.asyncio
async def test_dev_cors_allows_vite_origins(client: AsyncClient) -> None:
    response = await client.options(
        "/api/v2/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
