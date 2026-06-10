from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.abp import (
    AuditBundleV2,
    AuditRootsV2,
    BatchTallyPublicSignalsV2,
    CandidateV2,
    CastBallotRecordV2,
    ChallengeBallotRecordV2,
    CredentialV2,
    ElectionManifestV2,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def sample_candidate() -> CandidateV2:
    return CandidateV2(
        candidate_id="candidate_1",
        name="Candidate A",
        description="Baseline candidate",
        index=0,
    )


def sample_manifest() -> ElectionManifestV2:
    return ElectionManifestV2(
        election_id="election_1",
        election_id_hash="hash_election_1",
        title="ABP v2 model test",
        description="model baseline",
        candidates=[sample_candidate()],
        candidate_count=1,
        rule_hash="hash_rules",
        eligibility_root=None,
        tally_public_key=None,
        generator_context_hash="hash_generators",
        created_at=NOW,
    )


def sample_cast_ballot() -> CastBallotRecordV2:
    return CastBallotRecordV2(
        ballot_id="ballot_1",
        election_id_hash="hash_election_1",
        commitment="commitment_v2",
        nullifier_hash="nullifier_1",
        sealed_vote_package={"ciphertext": "sealed-value", "alg": "demo-seal-v1"},
        validity_proof_hash="proof_hash_1",
        receipt_code="receipt_1",
        receipt_chain_hash="receipt_chain_1",
        created_at=NOW,
    )


def sample_challenge_ballot() -> ChallengeBallotRecordV2:
    return ChallengeBallotRecordV2(
        ballot_id="challenge_1",
        election_id_hash="hash_election_1",
        commitment="commitment_v2",
        vote_vector=[1],
        randomness="opening-randomness",
        receipt_code="receipt_challenge_1",
        receipt_chain_hash="receipt_chain_challenge_1",
        created_at=NOW,
    )


def sample_roots() -> AuditRootsV2:
    return AuditRootsV2(
        manifest_hash="hash_manifest",
        eligibility_root=None,
        commitment_root="root_commitment",
        nullifier_root="root_nullifier",
        receipt_root="root_receipt",
        tally_hash="hash_tally",
        audit_bundle_hash="hash_bundle",
    )


def sample_bundle() -> AuditBundleV2:
    return AuditBundleV2(
        manifest=sample_manifest(),
        roots=sample_roots(),
        cast_ballots_public=[sample_cast_ballot()],
        challenge_records=[sample_challenge_ballot()],
        tally=[1],
        batch_proofs=[{"proof_hash": "proof_1"}],
        chain_record={"transaction_hash": "0xabc"},
        artifact_hash="artifact_hash_1",
    )


def test_cast_ballot_record_v2_accepts_public_sample() -> None:
    ballot = sample_cast_ballot()

    assert ballot.status == "cast"
    dumped = ballot.model_dump(mode="json")
    assert "candidate_id" not in dumped
    assert "vote_vector" not in dumped
    assert "randomness" not in dumped


@pytest.mark.parametrize("field_name", ["candidate_id", "vote_vector", "randomness"])
def test_cast_ballot_record_v2_rejects_plaintext_extra_fields(field_name: str) -> None:
    payload = sample_cast_ballot().model_dump()
    payload[field_name] = "forbidden"

    with pytest.raises(ValidationError):
        CastBallotRecordV2(**payload)


@pytest.mark.parametrize("field_name", ["candidate_id", "vote_vector", "randomness"])
def test_cast_ballot_record_v2_rejects_plaintext_inside_sealed_package(field_name: str) -> None:
    payload = sample_cast_ballot().model_dump()
    payload["sealed_vote_package"] = {"ciphertext": "sealed-value", field_name: "forbidden"}

    with pytest.raises(ValidationError):
        CastBallotRecordV2(**payload)


def test_challenge_ballot_record_v2_allows_opening_fields() -> None:
    challenge = sample_challenge_ballot()

    assert challenge.status == "challenged"
    assert challenge.vote_vector == [1]
    assert challenge.randomness == "opening-randomness"


def test_credential_v2_rejects_credential_secret() -> None:
    with pytest.raises(ValidationError):
        CredentialV2(
            credential_id="credential_1",
            credential_commitment="commitment_1",
            eligibility_merkle_path=None,
            credential_secret="secret",
        )


def test_audit_bundle_v2_serialization_excludes_credential_secret() -> None:
    serialized = sample_bundle().model_dump_json()

    assert "credential_secret" not in serialized


def test_audit_bundle_v2_serialization_excludes_tally_private_key() -> None:
    serialized = sample_bundle().model_dump_json()

    assert "tally_private_key" not in serialized


def test_audit_bundle_v2_rejects_private_chain_record_keys() -> None:
    with pytest.raises(ValidationError):
        AuditBundleV2(
            manifest=sample_manifest(),
            roots=sample_roots(),
            cast_ballots_public=[sample_cast_ballot()],
            challenge_records=[],
            tally=[1],
            batch_proofs=None,
            chain_record={"tally_private_key": "secret"},
            artifact_hash=None,
        )


def test_audit_bundle_v2_cast_ballots_public_exclude_plaintext_vote_fields() -> None:
    bundle = sample_bundle()
    cast_public = bundle.model_dump(mode="json")["cast_ballots_public"][0]

    assert "candidate_id" not in cast_public
    assert "vote_vector" not in cast_public
    assert "randomness" not in cast_public


def test_batch_tally_public_signals_v2_order_is_stable() -> None:
    signals = BatchTallyPublicSignalsV2(
        election_id_hash="election_hash",
        manifest_hash="manifest_hash",
        commitment_root="commitment_root",
        nullifier_root="nullifier_root",
        receipt_root="receipt_root",
        tally_hash="tally_hash",
        batch_index=2,
        batch_size=32,
    )

    assert signals.as_ordered_list() == [
        "election_hash",
        "manifest_hash",
        "commitment_root",
        "nullifier_root",
        "receipt_root",
        "tally_hash",
        2,
        32,
    ]


def test_election_manifest_v2_serializes_to_stable_json() -> None:
    manifest = sample_manifest()

    assert manifest.model_dump_json() == manifest.model_dump_json()


def test_election_manifest_v2_rejects_candidate_count_mismatch() -> None:
    with pytest.raises(ValidationError):
        ElectionManifestV2(
            election_id="election_1",
            election_id_hash="hash_election_1",
            title="ABP v2 model test",
            candidates=[sample_candidate()],
            candidate_count=2,
            rule_hash="hash_rules",
            generator_context_hash="hash_generators",
            created_at=NOW,
        )
