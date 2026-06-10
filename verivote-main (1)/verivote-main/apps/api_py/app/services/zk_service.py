from app.core.config import Settings
from app.core.security import ensure_zk_mock_mode_allowed
from app.models.abp import PrivateValidVoteProofV1
from app.zk.private_valid_vote import (
    PRIVATE_VALID_VOTE_CIRCUIT,
    ZK_PROFILE,
    PrivateValidVoteArtifactPaths,
    snarkjs_available,
    verify_private_valid_vote_proof,
)


class ZkService:
    def __init__(self, settings: Settings) -> None:
        ensure_zk_mock_mode_allowed(settings)
        self.settings = settings

    def status(self) -> dict:
        return {
            "zk_mock_mode": self.settings.zk_mock_mode,
            "message": "ZK service is a Python baseline placeholder",
        }

    def private_valid_vote_status(self) -> dict:
        paths = PrivateValidVoteArtifactPaths.from_settings(self.settings)
        verifier_artifact_present = paths.verifier_artifact_present
        snarkjs_ok = snarkjs_available(self.settings)
        real_available = verifier_artifact_present and snarkjs_ok
        configured = self.settings.zk_mock_mode or real_available
        warnings: list[str] = []
        if self.settings.zk_mock_mode:
            warnings.append("mock verifier enabled; mock is not a real proof")
        if not verifier_artifact_present:
            warnings.append("artifacts missing: verification_key.json is not configured")
        if not snarkjs_ok:
            warnings.append("snarkjs unavailable")
        warnings.append("SHA reference hash and Poseidon circuit profile alignment is pending")

        return {
            "configured": configured,
            "zk_profile": ZK_PROFILE,
            "circuit": PRIVATE_VALID_VOTE_CIRCUIT,
            "verifier_artifact_present": verifier_artifact_present,
            "snarkjs_available": snarkjs_ok,
            "mock_mode": self.settings.zk_mock_mode,
            "real_verifier_available": real_available,
            "warning": "; ".join(warnings),
        }

    def verify_private_valid_vote(self, proof: PrivateValidVoteProofV1) -> bool:
        return verify_private_valid_vote_proof(
            proof=proof,
            public_signals=proof.public_signals,
            settings=self.settings,
        )
