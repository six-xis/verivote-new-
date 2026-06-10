import json

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.errors import DomainError
from app.main import create_app
from app.models.abp import PrivateValidVoteProofV1, PrivateValidVotePublicSignalsV1
from app.zk.private_valid_vote import (
    PrivateValidVoteArtifactPaths,
    real_verifier_available,
    snarkjs_available,
    verify_private_valid_vote_proof,
    verify_private_valid_vote_proof_real,
)


def sample_public_signals() -> PrivateValidVotePublicSignalsV1:
    return PrivateValidVotePublicSignalsV1(
        election_id_hash="11",
        eligibility_root="13",
        nullifier_hash="17",
        commitment="19",
        rule_hash="23",
    )


def sample_mock_proof() -> PrivateValidVoteProofV1:
    return PrivateValidVoteProofV1(
        proof={"pi_a": ["mock"]},
        public_signals=sample_public_signals(),
        proof_system="mock-groth16",
        mock=True,
    )


def test_real_verifier_available_false_when_artifacts_are_missing(tmp_path) -> None:
    settings = Settings(
        app_mode="test",
        zk_mock_mode=False,
        zk_private_valid_vote_artifacts_dir=str(tmp_path / "missing"),
    )

    assert PrivateValidVoteArtifactPaths.from_settings(settings).verifier_artifact_present is False
    assert real_verifier_available(settings) is False


@pytest.mark.asyncio
async def test_zk_status_api_reports_missing_real_verifier_artifact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("VERIVOTE_APP_MODE", "test")
    monkeypatch.setenv("VERIVOTE_ZK_MOCK_MODE", "false")
    monkeypatch.setenv(
        "VERIVOTE_ZK_PRIVATE_VALID_VOTE_ARTIFACTS_DIR",
        str(tmp_path / "missing"),
    )
    get_settings.cache_clear()

    try:
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/api/v2/zk/private-valid-vote/status")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["zk_profile"] == "poseidon-v1"
    assert body["circuit"] == "private_valid_vote_4_8"
    assert body["verifier_artifact_present"] is False
    assert body["real_verifier_available"] is False
    assert "artifacts missing" in body["warning"]
    assert "SHA reference hash and Poseidon circuit profile alignment is pending" in body["warning"]


def test_verify_without_mock_and_missing_artifact_raises_not_configured(tmp_path) -> None:
    proof = sample_mock_proof()
    settings = Settings(
        app_mode="test",
        zk_mock_mode=False,
        zk_private_valid_vote_artifacts_dir=str(tmp_path / "missing"),
    )

    with pytest.raises(DomainError, match="real private valid vote verifier not configured"):
        verify_private_valid_vote_proof(proof, proof.public_signals, settings)


@pytest.mark.parametrize("app_mode", ["competition", "production"])
def test_competition_and_production_do_not_fallback_to_mock(app_mode: str) -> None:
    proof = sample_mock_proof()
    settings = Settings(app_mode=app_mode, zk_mock_mode=True)

    with pytest.raises(DomainError, match="forbidden"):
        verify_private_valid_vote_proof(proof, proof.public_signals, settings)


def test_public_signal_order_remains_the_m6a_contract() -> None:
    assert sample_public_signals().as_ordered_list() == [
        "11",
        "13",
        "17",
        "19",
        "23",
    ]


@pytest.mark.parametrize(
    "private_key",
    ["vote_vector", "randomness", "candidate_id", "credential_secret"],
)
def test_proof_schema_rejects_private_witness_keys(private_key: str) -> None:
    with pytest.raises(ValidationError):
        PrivateValidVoteProofV1(
            proof={private_key: "forbidden"},
            public_signals=sample_public_signals(),
            proof_system="groth16",
            mock=False,
        )


def test_real_verify_runs_when_snarkjs_and_artifacts_are_present() -> None:
    settings = Settings(app_mode="test", zk_mock_mode=False)
    paths = PrivateValidVoteArtifactPaths.from_settings(settings)

    if not paths.verifier_artifact_present:
        pytest.skip("private_valid_vote verification_key.json artifact is not present")
    if not snarkjs_available(settings):
        pytest.skip("snarkjs command is not available")
    if not paths.proof.is_file() or not paths.public.is_file():
        pytest.skip("private_valid_vote proof.json/public.json artifacts are not present")

    public_values = json.loads(paths.public.read_text(encoding="utf-8"))
    assert len(public_values) == 5
    public_signals = PrivateValidVotePublicSignalsV1(
        election_id_hash=public_values[0],
        eligibility_root=public_values[1],
        nullifier_hash=public_values[2],
        commitment=public_values[3],
        rule_hash=public_values[4],
    )
    proof = PrivateValidVoteProofV1(
        proof=json.loads(paths.proof.read_text(encoding="utf-8")),
        public_signals=public_signals,
        proof_system="groth16",
        mock=False,
    )

    assert verify_private_valid_vote_proof_real(proof, public_signals, settings) is True
