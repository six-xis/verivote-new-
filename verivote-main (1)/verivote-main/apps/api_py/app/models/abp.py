from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ElectionStatus = Literal["active", "finalized"]
BallotPrivacyMode = Literal["legacy_simple", "abp_v2_reserved"]


class Election(BaseModel):
    id: str
    title: str
    description: str = ""
    status: ElectionStatus = "active"
    eligibility_root: str | None = None
    created_at: str


class Candidate(BaseModel):
    id: str
    election_id: str
    name: str
    description: str = ""


class DemoCredential(BaseModel):
    id: str
    election_id: str
    user_id: str
    credential_commitment: str
    created_at: str


class LegacyBallot(BaseModel):
    id: str
    election_id: str
    user_id: str
    candidate_id: str
    vote_vector: list[int]
    randomness: str
    commitment: str
    receipt_code: str
    receipt_chain_index: int
    previous_receipt_code_hash: str | None
    receipt_chain_hash: str
    created_at: str
    privacy_mode: BallotPrivacyMode = "legacy_simple"


class TallyResultItem(BaseModel):
    candidate_id: str
    candidate_name: str
    vote_count: int


class ReceiptChainBreak(BaseModel):
    ballot_id: str | None = None
    index: int
    reason: str


class AuditReport(BaseModel):
    election_id: str
    total_ballots: int
    valid_ballots: int
    invalid_ballots: int
    duplicate_ballots: int
    receipt_chain_verified: bool
    receipt_chain_breaks: list[ReceiptChainBreak] = Field(default_factory=list)
    commitment_openings_verified: bool
    commitment_opening_failures: list[str] = Field(default_factory=list)
    commitment_root: str
    nullifier_root: str
    receipt_root: str
    tally_hash: str
    audit_bundle_hash: str
    tally: list[TallyResultItem]
    status: Literal["passed", "failed"]
    created_at: str


class AttackMutation(BaseModel):
    id: str
    election_id: str
    attack_type: str
    before: dict
    after: dict
    created_at: str


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CandidateV2(StrictModel):
    candidate_id: str
    name: str
    description: str | None = None
    index: int


class ElectionManifestV2(StrictModel):
    version: Literal["verivote-abp-v1"] = "verivote-abp-v1"
    election_id: str
    election_id_hash: str
    title: str
    description: str | None = None
    candidates: list[CandidateV2]
    candidate_count: int
    rule_hash: str
    eligibility_root: str | None = None
    tally_public_key: str | None = None
    generator_context_hash: str
    created_at: datetime

    @model_validator(mode="after")
    def candidate_count_matches_candidates(self) -> "ElectionManifestV2":
        if self.candidate_count != len(self.candidates):
            raise ValueError("candidate_count must match candidates length")
        return self


class CredentialV2(StrictModel):
    credential_id: str
    credential_commitment: str
    eligibility_merkle_path: list[dict[str, str]] | None = None


class DemoCredentialRecordV2(StrictModel):
    credential_id: str
    election_id: str
    credential_secret: str
    credential_commitment: str
    issued_at: str


class DemoCredentialIssueResponse(StrictModel):
    credential_id: str
    credential_secret: str
    credential_commitment: str
    eligibility_root: str
    warning: str

    @model_validator(mode="after")
    def warning_mentions_demo_only(self) -> "DemoCredentialIssueResponse":
        normalized = self.warning.lower()
        if "demo only" not in normalized and "demo-only" not in normalized:
            raise ValueError("warning must state that this credential is demo only")
        return self


CAST_BALLOT_PRIVATE_KEYS = {"candidate_id", "vote_vector", "randomness"}


def _find_keys(value: Any, forbidden: set[str], path: str = "$") -> list[str]:
    if isinstance(value, dict):
        findings: list[str] = []
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in forbidden:
                findings.append(child_path)
            findings.extend(_find_keys(child, forbidden, child_path))
        return findings
    if isinstance(value, list):
        findings = []
        for index, child in enumerate(value):
            findings.extend(_find_keys(child, forbidden, f"{path}[{index}]"))
        return findings
    return []


class CastBallotRecordV2(StrictModel):
    ballot_id: str
    election_id_hash: str
    commitment: str
    nullifier_hash: str
    sealed_vote_package: dict[str, Any]
    sealed_vote_package_hash: str | None = None
    validity_proof_hash: str | None = None
    receipt_code: str
    receipt_chain_hash: str
    status: Literal["cast"] = "cast"
    created_at: datetime

    @model_validator(mode="after")
    def reject_plaintext_vote_fields(self) -> "CastBallotRecordV2":
        findings = _find_keys(self.sealed_vote_package, CAST_BALLOT_PRIVATE_KEYS)
        if findings:
            raise ValueError(
                "CastBallotRecordV2 sealed_vote_package contains plaintext vote keys: "
                + ", ".join(findings)
            )
        return self


class ChallengeBallotRecordV2(StrictModel):
    ballot_id: str
    election_id_hash: str
    commitment: str
    vote_vector: list[int]
    randomness: str
    receipt_code: str
    receipt_chain_hash: str
    status: Literal["challenged"] = "challenged"
    created_at: datetime


class AuditRootsV2(StrictModel):
    manifest_hash: str
    eligibility_root: str | None = None
    commitment_root: str
    nullifier_root: str
    receipt_root: str
    tally_hash: str | None = None
    audit_bundle_hash: str | None = None


class BatchTallyPublicSignalsV2(StrictModel):
    """Public signal order consumed by circuits and Solidity verifiers.

    Fixed order:
    0 election_id_hash
    1 manifest_hash
    2 commitment_root
    3 nullifier_root
    4 receipt_root
    5 tally_hash
    6 batch_index
    7 batch_size
    """

    election_id_hash: str
    manifest_hash: str
    commitment_root: str
    nullifier_root: str
    receipt_root: str
    tally_hash: str
    batch_index: int
    batch_size: int

    def as_ordered_list(self) -> list[str | int]:
        return [
            self.election_id_hash,
            self.manifest_hash,
            self.commitment_root,
            self.nullifier_root,
            self.receipt_root,
            self.tally_hash,
            self.batch_index,
            self.batch_size,
        ]


PRIVATE_VALID_VOTE_PRIVATE_KEYS = {
    "candidate_id",
    "credential_secret",
    "randomness",
    "vote_vector",
}


class PrivateValidVotePublicSignalsV1(StrictModel):
    """Public signals consumed by the future private valid vote verifier.

    Fixed order:
    0 election_id_hash
    1 eligibility_root
    2 nullifier_hash
    3 commitment
    4 rule_hash
    """

    election_id_hash: str
    eligibility_root: str | None
    nullifier_hash: str
    commitment: str
    rule_hash: str | None = None

    def as_ordered_list(self) -> list[str | None]:
        return [
            self.election_id_hash,
            self.eligibility_root,
            self.nullifier_hash,
            self.commitment,
            self.rule_hash,
        ]


class PrivateValidVoteProofV1(StrictModel):
    proof: dict[str, Any]
    public_signals: PrivateValidVotePublicSignalsV1
    proof_system: str = "mock-groth16"
    artifact_hash: str | None = None
    mock: bool = False

    @model_validator(mode="after")
    def reject_mock_flag_without_mock_proof_system(self) -> "PrivateValidVoteProofV1":
        if self.mock and "mock" not in self.proof_system.lower():
            raise ValueError("mock proofs must use a proof_system containing 'mock'")

        findings = _find_keys(self.proof, PRIVATE_VALID_VOTE_PRIVATE_KEYS)
        if findings:
            raise ValueError(
                "PrivateValidVoteProofV1 proof contains private witness keys: "
                + ", ".join(findings)
            )
        return self


FORBIDDEN_AUDIT_BUNDLE_KEYS = {
    "credential_secret",
    "tally_private_key",
    "decrypted_openings",
    "decrypted_cast_openings",
    "cast_candidate_id",
    "cast_vote_vector",
    "cast_randomness",
}


def _find_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    return _find_keys(value, FORBIDDEN_AUDIT_BUNDLE_KEYS, path)


class AuditBundleV2(StrictModel):
    version: Literal["verivote-abp-v1"] = "verivote-abp-v1"
    manifest: ElectionManifestV2
    roots: AuditRootsV2
    cast_ballots_public: list[CastBallotRecordV2]
    challenge_records: list[ChallengeBallotRecordV2]
    tally: list[int] | None = None
    batch_proofs: list[dict[str, Any]] | None = None
    chain_record: dict[str, Any] | None = None
    artifact_hash: str | None = None

    @model_validator(mode="after")
    def reject_private_artifact_keys(self) -> "AuditBundleV2":
        findings = _find_forbidden_keys(
            {
                "batch_proofs": self.batch_proofs,
                "chain_record": self.chain_record,
            }
        )
        if findings:
            raise ValueError(
                "AuditBundleV2 contains forbidden private keys: " + ", ".join(findings)
            )
        return self
