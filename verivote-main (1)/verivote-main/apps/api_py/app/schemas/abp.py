from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.crypto.sealed_vote import compute_sealed_vote_package_hash
from app.models.abp import (
    AuditBundleV2,
    AuditReport,
    AuditRootsV2,
    BatchTallyPublicSignalsV2,
    Candidate,
    CandidateV2,
    CastBallotRecordV2,
    ChallengeBallotRecordV2,
    CredentialV2,
    DemoCredential,
    DemoCredentialIssueResponse as DemoCredentialIssuePayload,
    Election,
    ElectionManifestV2,
    LegacyBallot,
    PrivateValidVoteProofV1,
    PrivateValidVotePublicSignalsV1,
)


CAST_BALLOT_PRIVATE_KEYS = {"candidate_id", "vote_vector", "randomness"}


def _find_private_keys(value: Any, path: str = "$") -> list[str]:
    if isinstance(value, dict):
        findings: list[str] = []
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in CAST_BALLOT_PRIVATE_KEYS:
                findings.append(child_path)
            findings.extend(_find_private_keys(child, child_path))
        return findings
    if isinstance(value, list):
        findings = []
        for index, child in enumerate(value):
            findings.extend(_find_private_keys(child, f"{path}[{index}]"))
        return findings
    return []


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StatusResponse(StrictSchema):
    ok: bool
    service: str
    mode: str | None = None
    legacy: bool = False


class CreateElectionRequest(StrictSchema):
    title: str = Field(min_length=1)
    description: str = ""


class ElectionResponse(StrictSchema):
    election: Election


class CandidatePublicSummary(StrictSchema):
    id: str
    election_id: str
    electionId: str
    name: str
    description: str | None = None
    index: int


class ElectionPublicSummary(StrictSchema):
    id: str
    election_id: str
    election_id_hash: str
    title: str
    description: str | None = None
    status: str
    candidate_count: int
    eligibility_root: str | None = None
    created_at: str
    createdAt: str


class ElectionPublicDetail(ElectionPublicSummary):
    candidates: list[CandidatePublicSummary]


class ElectionListResponse(StrictSchema):
    elections: list[ElectionPublicSummary]


class ElectionDetailResponse(StrictSchema):
    election: ElectionPublicDetail


class CreateCandidateRequest(StrictSchema):
    name: str = Field(min_length=1)
    description: str = ""


class CandidateResponse(StrictSchema):
    candidate: Candidate


class DemoRegisterRequest(StrictSchema):
    user_id: str = Field(min_length=1)


class DemoCredentialResponse(StrictSchema):
    credential: DemoCredential
    message: str


class LegacyCastBallotRequest(StrictSchema):
    user_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)


class LegacyCastBallotResponse(StrictSchema):
    ballot_id: str
    receipt_code: str
    commitment: str
    receipt_chain_hash: str
    message: str
    ballot: LegacyBallot


class LegacyVotePublicRequest(StrictSchema):
    user_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)


class LegacyVotePublicResponse(StrictSchema):
    vote_id: str
    voteId: str
    receipt_code: str
    receiptCode: str
    commitment: str
    receipt_chain_index: int
    receiptChainIndex: int
    previous_receipt_code_hash: str | None = None
    previousReceiptCodeHash: str | None = None
    receipt_chain_hash: str
    receiptChainHash: str
    message: str


class CastBallotRequestV2(StrictSchema):
    commitment: str = Field(min_length=1)
    nullifier_hash: str = Field(min_length=1)
    sealed_vote_package: dict[str, Any]
    sealed_vote_package_hash: str = Field(min_length=1)
    receipt_code: str = Field(min_length=1)
    validity_proof_hash: str | None = None
    validity_proof: PrivateValidVoteProofV1 | None = None

    @field_validator("commitment", "nullifier_hash", "sealed_vote_package_hash", "receipt_code")
    @classmethod
    def non_empty_string(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("field must not be empty")
        return normalized

    @field_validator("validity_proof_hash")
    @classmethod
    def optional_non_empty_string(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("validity_proof_hash must not be empty when provided")
        return normalized

    @model_validator(mode="after")
    def validate_sealed_vote_package_boundary(self) -> "CastBallotRequestV2":
        private_keys = _find_private_keys(self.sealed_vote_package)
        if private_keys:
            raise ValueError(
                "sealed_vote_package contains plaintext vote keys: " + ", ".join(private_keys)
            )

        computed_hash = compute_sealed_vote_package_hash(self.sealed_vote_package)
        if computed_hash != self.sealed_vote_package_hash:
            raise ValueError("sealed_vote_package_hash does not match sealed_vote_package")
        return self


class CastBallotResponseV2(StrictSchema):
    ballot_id: str
    election_id_hash: str
    commitment: str
    nullifier_hash: str
    sealed_vote_package_hash: str
    validity_proof_hash: str | None = None
    receipt_code: str
    receipt_chain_hash: str
    status: Literal["cast"]
    created_at: str


class CastBallotPublicRecordV2(StrictSchema):
    ballot_id: str
    election_id_hash: str
    commitment: str
    nullifier_hash: str
    sealed_vote_package_hash: str
    validity_proof_hash: str | None = None
    receipt_code: str
    receipt_chain_hash: str
    status: Literal["cast"]
    created_at: str


class PrivateValidVotePublicSignalsV1Response(StrictSchema):
    public_signals: PrivateValidVotePublicSignalsV1
    ordered_public_signals: list[str | None]


class PrivateValidVoteStatusResponse(StrictSchema):
    configured: bool
    zk_profile: Literal["poseidon-v1"]
    circuit: str
    verifier_artifact_present: bool
    snarkjs_available: bool
    mock_mode: bool
    real_verifier_available: bool
    warning: str


class BulletinBoardResponseV2(StrictSchema):
    election_id: str
    election_id_hash: str
    manifest: ElectionManifestV2
    cast_ballots_public: list[CastBallotPublicRecordV2]
    challenge_records: list[ChallengeBallotRecordV2]
    roots: AuditRootsV2 | None = None


class AuditReportResponse(StrictSchema):
    report: AuditReport


class AttackResponse(StrictSchema):
    ok: bool
    attack_type: str
    mutation_id: str
    message: str


class ElectionManifestV2Response(StrictSchema):
    manifest: ElectionManifestV2


class CandidateV2ListResponse(StrictSchema):
    candidates: list[CandidateV2]


class CredentialV2Response(StrictSchema):
    credential: CredentialV2


class DemoCredentialIssueEnvelope(StrictSchema):
    credential: DemoCredentialIssuePayload


class PublicCredentialsResponseV2(StrictSchema):
    eligibility_root: str
    credentials: list[CredentialV2]


class DeriveNullifierRequestV2(StrictSchema):
    credential_secret: str = Field(min_length=1)

    @field_validator("credential_secret")
    @classmethod
    def credential_secret_must_not_be_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("credential_secret must not be empty")
        return normalized


class DeriveNullifierResponseV2(StrictSchema):
    nullifier_hash: str
    warning: str


class CastBallotRecordV2Response(StrictSchema):
    ballot: CastBallotRecordV2


class ChallengeBallotRecordV2Response(StrictSchema):
    challenge_record: ChallengeBallotRecordV2


class AuditRootsV2Response(StrictSchema):
    roots: AuditRootsV2


class BatchTallyPublicSignalsV2Response(StrictSchema):
    public_signals: BatchTallyPublicSignalsV2
    ordered_public_signals: list[str | int]


class AuditBundleV2Response(StrictSchema):
    bundle: AuditBundleV2
