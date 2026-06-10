import json
import os
import shlex
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.core.errors import DomainError
from app.models.abp import (
    PRIVATE_VALID_VOTE_PRIVATE_KEYS,
    PrivateValidVoteProofV1,
    PrivateValidVotePublicSignalsV1,
)


ZK_PROFILE = "poseidon-v1"
PRIVATE_VALID_VOTE_CIRCUIT = "private_valid_vote_4_8"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class PrivateValidVoteArtifactPaths:
    artifacts_dir: Path
    verification_key: Path
    proof: Path
    public: Path
    zkey: Path
    witness: Path

    @classmethod
    def from_settings(cls, settings: Settings) -> "PrivateValidVoteArtifactPaths":
        configured = Path(settings.zk_private_valid_vote_artifacts_dir)
        if configured.is_absolute():
            artifacts_dir = configured
        else:
            cwd_candidate = (Path.cwd() / configured).resolve()
            repo_candidate = (_repo_root() / configured).resolve()
            artifacts_dir = cwd_candidate if cwd_candidate.exists() else repo_candidate

        return cls(
            artifacts_dir=artifacts_dir,
            verification_key=artifacts_dir / "verification_key.json",
            proof=artifacts_dir / "proof.json",
            public=artifacts_dir / "public.json",
            zkey=artifacts_dir / "private_valid_vote.zkey",
            witness=artifacts_dir / "witness.wtns",
        )

    @property
    def verifier_artifact_present(self) -> bool:
        return self.verification_key.is_file()


def _snarkjs_command(settings: Settings) -> list[str]:
    command = shlex.split(settings.zk_snarkjs_command)
    if not command:
        raise DomainError(501, "real private valid vote verifier not configured: empty snarkjs command")
    if os.name == "nt" and command[0] == "pnpm" and shutil.which("pnpm.cmd"):
        command[0] = "pnpm.cmd"
    return command


def snarkjs_available(settings: Settings) -> bool:
    command = _snarkjs_command(settings)
    if shutil.which(command[0]) is None:
        return False

    try:
        result = subprocess.run(
            command,
            cwd=_repo_root(),
            capture_output=True,
            text=True,
            timeout=min(settings.zk_snarkjs_timeout_seconds, 10),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    return result.returncode == 0 or "snarkjs" in combined_output


def real_verifier_available(settings: Settings) -> bool:
    paths = PrivateValidVoteArtifactPaths.from_settings(settings)
    return paths.verifier_artifact_present and snarkjs_available(settings)


def _find_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    if isinstance(value, dict):
        findings: list[str] = []
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in PRIVATE_VALID_VOTE_PRIVATE_KEYS:
                findings.append(child_path)
            findings.extend(_find_forbidden_keys(child, child_path))
        return findings
    if isinstance(value, list):
        findings = []
        for index, child in enumerate(value):
            findings.extend(_find_forbidden_keys(child, f"{path}[{index}]"))
        return findings
    return []


def assert_private_valid_vote_public_signals_safe(
    public_signals: PrivateValidVotePublicSignalsV1 | dict[str, Any],
) -> PrivateValidVotePublicSignalsV1:
    parsed = (
        public_signals
        if isinstance(public_signals, PrivateValidVotePublicSignalsV1)
        else PrivateValidVotePublicSignalsV1(**public_signals)
    )
    findings = _find_forbidden_keys(parsed.model_dump(mode="json"))
    if findings:
        raise DomainError(
            400,
            "private valid vote public_signals contain forbidden private keys: "
            + ", ".join(findings),
        )
    return parsed


def _snarkjs_public_signals(public_signals: PrivateValidVotePublicSignalsV1) -> list[str]:
    ordered = public_signals.as_ordered_list()
    if any(value is None for value in ordered):
        raise DomainError(400, "real private valid vote verifier requires all public signals")
    return [str(value) for value in ordered]


def verify_private_valid_vote_proof_real(
    proof: PrivateValidVoteProofV1 | dict[str, Any],
    public_signals: PrivateValidVotePublicSignalsV1 | dict[str, Any],
    settings: Settings,
) -> bool:
    parsed_proof = proof if isinstance(proof, PrivateValidVoteProofV1) else PrivateValidVoteProofV1(**proof)
    parsed_signals = assert_private_valid_vote_public_signals_safe(public_signals)
    if parsed_signals != parsed_proof.public_signals:
        raise DomainError(400, "proof public_signals do not match the supplied public_signals")

    paths = PrivateValidVoteArtifactPaths.from_settings(settings)
    if not paths.verifier_artifact_present:
        raise DomainError(
            501,
            "real private valid vote verifier not configured: "
            f"missing verification_key.json at {paths.verification_key}",
        )
    if not snarkjs_available(settings):
        raise DomainError(501, "real private valid vote verifier not configured: snarkjs unavailable")
    if parsed_proof.mock or "mock" in parsed_proof.proof_system.lower():
        raise DomainError(400, "real private valid vote verifier requires a non-mock proof")

    public_values = _snarkjs_public_signals(parsed_signals)
    command = _snarkjs_command(settings)

    with tempfile.TemporaryDirectory(prefix="verivote-private-valid-vote-") as tmpdir:
        tmp_path = Path(tmpdir)
        public_path = tmp_path / "public.json"
        proof_path = tmp_path / "proof.json"
        public_path.write_text(json.dumps(public_values), encoding="utf-8")
        proof_path.write_text(json.dumps(parsed_proof.proof), encoding="utf-8")

        result = subprocess.run(
            command
            + [
                "groth16",
                "verify",
                str(paths.verification_key),
                str(public_path),
                str(proof_path),
            ],
            cwd=_repo_root(),
            capture_output=True,
            text=True,
            timeout=settings.zk_snarkjs_timeout_seconds,
            check=False,
        )

    return result.returncode == 0


def verify_private_valid_vote_proof(
    proof: PrivateValidVoteProofV1 | dict[str, Any],
    public_signals: PrivateValidVotePublicSignalsV1 | dict[str, Any] | None,
    settings: Settings,
) -> bool:
    parsed_proof = proof if isinstance(proof, PrivateValidVoteProofV1) else PrivateValidVoteProofV1(**proof)
    parsed_signals = assert_private_valid_vote_public_signals_safe(
        parsed_proof.public_signals if public_signals is None else public_signals
    )
    if parsed_signals != parsed_proof.public_signals:
        raise DomainError(400, "proof public_signals do not match the supplied public_signals")

    if settings.zk_mock_mode:
        if settings.app_mode in {"competition", "production"}:
            raise DomainError(
                403,
                "ZK mock verifier is forbidden in competition or production mode",
            )
        if settings.app_mode not in {"test", "development"}:
            raise DomainError(403, "ZK mock verifier is only allowed in test/development mode")
        if not parsed_proof.mock and "mock" not in parsed_proof.proof_system.lower():
            raise DomainError(400, "mock mode requires proof.mock=true or a mock proof_system")
        return True

    return verify_private_valid_vote_proof_real(parsed_proof, parsed_signals, settings)
