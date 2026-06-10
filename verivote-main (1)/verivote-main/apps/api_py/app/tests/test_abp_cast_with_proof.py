import json
from copy import deepcopy
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.crypto.commitment_v2 import compute_commitment_v2
from app.crypto.sealed_vote import compute_sealed_vote_package_hash, seal_vote_opening
from app.main import create_app


DEMO_TALLY_KEY = "phase5-proof-demo-key"


@pytest_asyncio.fixture
async def mock_zk_client(monkeypatch: pytest.MonkeyPatch) -> AsyncClient:
    monkeypatch.setenv("VERIVOTE_APP_MODE", "test")
    monkeypatch.setenv("VERIVOTE_ZK_MOCK_MODE", "true")
    get_settings.cache_clear()
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client
    get_settings.cache_clear()


async def create_election_with_credential(client: AsyncClient) -> dict[str, Any]:
    election_response = await client.post(
        "/api/v2/elections",
        json={"title": "Proof cast election", "description": "phase5"},
    )
    assert election_response.status_code == 201
    election_id = election_response.json()["election"]["id"]

    for index in range(4):
        candidate_response = await client.post(
            f"/api/v2/elections/{election_id}/candidates",
            json={"name": f"Candidate {index + 1}", "description": "candidate"},
        )
        assert candidate_response.status_code == 201

    credential_response = await client.post(
        f"/api/v2/elections/{election_id}/credentials/demo-issue"
    )
    assert credential_response.status_code == 201
    board_response = await client.get(f"/api/v2/elections/{election_id}/bulletin-board")
    assert board_response.status_code == 200
    return {
        "election_id": election_id,
        "credential": credential_response.json(),
        "board": board_response.json(),
    }


def build_proven_cast_payload(
    board: dict[str, Any],
    nullifier_hash: str = "12345",
    proof_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    election_id_hash = board["election_id_hash"]
    manifest = board["manifest"]
    vote_vector = [1, 0, 0, 0]
    randomness = "phase5-proof-randomness"
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
    public_signals = {
        "election_id_hash": election_id_hash,
        "eligibility_root": manifest["eligibility_root"],
        "nullifier_hash": nullifier_hash,
        "commitment": commitment,
        "rule_hash": manifest["rule_hash"],
    }
    proof = {
        "proof": {"pi_a": ["mock"]},
        "public_signals": public_signals,
        "proof_system": "mock-groth16",
        "artifact_hash": "mock-artifact-hash",
        "mock": True,
    }
    if proof_overrides:
        proof = deep_merge(proof, proof_overrides)
    return {
        "commitment": commitment,
        "nullifier_hash": nullifier_hash,
        "sealed_vote_package": sealed_vote_package,
        "sealed_vote_package_hash": compute_sealed_vote_package_hash(sealed_vote_package),
        "receipt_code": "phase5-receipt-code",
        "validity_proof_hash": "mock-validity-proof-hash",
        "validity_proof": proof,
    }


def deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def assert_no_private_fields(value: Any) -> None:
    serialized = json.dumps(value)
    assert "vote_vector" not in serialized
    assert "randomness" not in serialized
    assert "candidate_id" not in serialized
    assert "credential_secret" not in serialized


def assert_no_private_ballot_fields_in_board(value: dict[str, Any]) -> None:
    serialized = json.dumps(value)
    assert "vote_vector" not in serialized
    assert "randomness" not in serialized
    assert "credential_secret" not in serialized
    assert "candidate_id" not in json.dumps(value["cast_ballots_public"])


@pytest.mark.asyncio
async def test_mock_private_valid_vote_proof_cast_succeeds(mock_zk_client: AsyncClient) -> None:
    context = await create_election_with_credential(mock_zk_client)
    payload = build_proven_cast_payload(context["board"])

    response = await mock_zk_client.post(
        f"/api/v2/elections/{context['election_id']}/ballots/cast",
        json=payload,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "cast"
    assert body["nullifier_hash"] == payload["nullifier_hash"]
    assert_no_private_fields(body)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("signal_name", "wrong_value"),
    [
        ("election_id_hash", "wrong-election"),
        ("eligibility_root", "wrong-root"),
        ("nullifier_hash", "99999"),
        ("commitment", "wrong-commitment"),
    ],
)
async def test_cast_rejects_mismatched_proof_public_signals(
    mock_zk_client: AsyncClient,
    signal_name: str,
    wrong_value: str,
) -> None:
    context = await create_election_with_credential(mock_zk_client)
    payload = build_proven_cast_payload(
        context["board"],
        proof_overrides={"public_signals": {signal_name: wrong_value}},
    )

    response = await mock_zk_client.post(
        f"/api/v2/elections/{context['election_id']}/ballots/cast",
        json=payload,
    )

    assert response.status_code in {400, 422}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field_name",
    ["vote_vector", "randomness", "candidate_id", "credential_secret"],
)
async def test_cast_rejects_private_fields_inside_public_signals(
    mock_zk_client: AsyncClient,
    field_name: str,
) -> None:
    context = await create_election_with_credential(mock_zk_client)
    payload = build_proven_cast_payload(
        context["board"],
        proof_overrides={"public_signals": {field_name: "forbidden"}},
    )

    response = await mock_zk_client.post(
        f"/api/v2/elections/{context['election_id']}/ballots/cast",
        json=payload,
    )

    assert response.status_code in {400, 422}


@pytest.mark.asyncio
async def test_cast_rejects_non_mock_proof_when_mock_mode_is_enabled(
    mock_zk_client: AsyncClient,
) -> None:
    context = await create_election_with_credential(mock_zk_client)
    payload = build_proven_cast_payload(
        context["board"],
        proof_overrides={"proof_system": "groth16", "mock": False},
    )

    response = await mock_zk_client.post(
        f"/api/v2/elections/{context['election_id']}/ballots/cast",
        json=payload,
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_proven_cast_bulletin_board_does_not_leak_private_fields(
    mock_zk_client: AsyncClient,
) -> None:
    context = await create_election_with_credential(mock_zk_client)
    payload = build_proven_cast_payload(context["board"])
    cast_response = await mock_zk_client.post(
        f"/api/v2/elections/{context['election_id']}/ballots/cast",
        json=payload,
    )
    assert cast_response.status_code == 201

    board_response = await mock_zk_client.get(
        f"/api/v2/elections/{context['election_id']}/bulletin-board"
    )

    assert board_response.status_code == 200
    assert_no_private_ballot_fields_in_board(board_response.json())
