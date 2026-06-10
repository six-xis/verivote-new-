import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import DomainError
from app.models.abp import PrivateValidVoteProofV1, PrivateValidVotePublicSignalsV1
from app.services.zk_service import ZkService


def sample_public_signals() -> PrivateValidVotePublicSignalsV1:
    return PrivateValidVotePublicSignalsV1(
        election_id_hash="election-hash",
        eligibility_root="eligibility-root",
        nullifier_hash="nullifier-hash",
        commitment="commitment",
        rule_hash="rule-hash",
    )


def sample_mock_proof() -> PrivateValidVoteProofV1:
    return PrivateValidVoteProofV1(
        proof={"pi_a": ["mock"]},
        public_signals=sample_public_signals(),
        proof_system="mock-groth16",
        mock=True,
    )


def test_private_valid_vote_public_signals_accept_public_fields() -> None:
    signals = sample_public_signals()

    assert signals.election_id_hash == "election-hash"


@pytest.mark.parametrize("field_name", ["vote_vector", "randomness", "candidate_id", "credential_secret"])
def test_private_valid_vote_public_signals_reject_private_fields(field_name: str) -> None:
    payload = sample_public_signals().model_dump()
    payload[field_name] = "forbidden"

    with pytest.raises(ValidationError):
        PrivateValidVotePublicSignalsV1(**payload)


def test_private_valid_vote_public_signals_order_is_stable() -> None:
    assert sample_public_signals().as_ordered_list() == [
        "election-hash",
        "eligibility-root",
        "nullifier-hash",
        "commitment",
        "rule-hash",
    ]


def test_mock_proof_verifies_in_test_mode_when_mock_enabled() -> None:
    service = ZkService(Settings(app_mode="test", zk_mock_mode=True))

    assert service.verify_private_valid_vote(sample_mock_proof()) is True


def test_real_verifier_reports_not_configured_when_mock_disabled_and_artifacts_missing(
    tmp_path,
) -> None:
    service = ZkService(
        Settings(
            app_mode="test",
            zk_mock_mode=False,
            zk_private_valid_vote_artifacts_dir=str(tmp_path / "missing"),
        )
    )

    with pytest.raises(DomainError, match="real private valid vote verifier not configured"):
        service.verify_private_valid_vote(sample_mock_proof())


@pytest.mark.parametrize("app_mode", ["competition", "production"])
def test_mock_verifier_is_rejected_in_competition_or_production(app_mode: str) -> None:
    with pytest.raises(DomainError, match="forbidden"):
        ZkService(Settings(app_mode=app_mode, zk_mock_mode=True))


@pytest.mark.asyncio
async def test_private_valid_vote_status_returns_warning(client: AsyncClient) -> None:
    response = await client.get("/api/v2/zk/private-valid-vote/status")

    assert response.status_code == 200
    body = response.json()
    assert body["verifier_artifact_present"] is True
    assert body["snarkjs_available"] is True
    assert body["real_verifier_available"] is True
    assert body["warning"]
