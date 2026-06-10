import secrets
from typing import Any

from app.core.errors import DomainError
from app.crypto.hash_utils import hash_object
from app.crypto.receipt_chain import (
    ReceiptChainInput,
    create_receipt_chain_hash,
    hash_receipt_code,
)
from app.crypto.sealed_vote import compute_sealed_vote_package_hash
from app.models.abp import CastBallotRecordV2, LegacyBallot, PrivateValidVoteProofV1
from app.repositories.memory import MemoryRepository
from app.services.election_service import ElectionService, utc_now


RECEIPT_CHAIN_GENESIS_V2 = "VERIVOTE_RECEIPT_GENESIS"


class BallotService:
    def __init__(self, repository: MemoryRepository, election_service: ElectionService) -> None:
        self.repository = repository
        self.election_service = election_service

    def legacy_cast(self, election_id: str, user_id: str, candidate_id: str) -> LegacyBallot:
        self.election_service.require_election(election_id)
        candidate = self.election_service.require_candidate_for_election(election_id, candidate_id)

        if self.repository.get_credential(election_id, user_id) is None:
            raise DomainError(404, "demo credential not found for user")

        for ballot in self.repository.list_ballots(election_id):
            if ballot.user_id == user_id:
                raise DomainError(409, "user has already cast a ballot in this election")

        candidates = self.election_service.list_candidates(election_id)
        candidate_ids = [item.id for item in candidates]
        vote_vector = [1 if item == candidate.id else 0 for item in candidate_ids]
        randomness = secrets.token_hex(32)
        commitment = create_legacy_commitment(election_id, vote_vector, randomness)
        created_at = utc_now()
        receipt_code = hash_object(
            "verivote.receipt_code.v1",
            {
                "election_id": election_id,
                "commitment": commitment,
                "user_id": user_id,
                "created_at": created_at,
            },
        )

        existing_ballots = sorted(
            self.repository.list_ballots(election_id),
            key=lambda ballot: ballot.receipt_chain_index,
        )
        previous = existing_ballots[-1] if existing_ballots else None
        previous_hash = None if previous is None else hash_receipt_code(previous.receipt_code)
        receipt_chain_index = len(existing_ballots)
        receipt_chain_hash = create_receipt_chain_hash(
            ReceiptChainInput(
                election_id=election_id,
                receipt_code=receipt_code,
                previous_receipt_code_hash=previous_hash,
                receipt_chain_index=receipt_chain_index,
                commitment=commitment,
            )
        )

        ballot = LegacyBallot(
            id=self.repository.create_id("ballot"),
            election_id=election_id,
            user_id=user_id,
            candidate_id=candidate.id,
            vote_vector=vote_vector,
            randomness=randomness,
            commitment=commitment,
            receipt_code=receipt_code,
            previous_receipt_code_hash=previous_hash,
            receipt_chain_index=receipt_chain_index,
            receipt_chain_hash=receipt_chain_hash,
            created_at=created_at,
        )
        return self.repository.save_ballot(ballot)

    def cast_v2(
        self,
        election_id: str,
        commitment: str,
        nullifier_hash: str,
        sealed_vote_package: dict[str, Any],
        sealed_vote_package_hash: str,
        receipt_code: str,
        validity_proof_hash: str | None = None,
        validity_proof: PrivateValidVoteProofV1 | None = None,
        zk_service: Any | None = None,
    ) -> CastBallotRecordV2:
        self.election_service.require_election(election_id)

        commitment = commitment.strip()
        nullifier_hash = nullifier_hash.strip()
        receipt_code = receipt_code.strip()
        sealed_vote_package_hash = sealed_vote_package_hash.strip()
        validity_proof_hash = (
            None if validity_proof_hash is None else validity_proof_hash.strip()
        )

        if not commitment:
            raise DomainError(400, "commitment must not be empty")
        if not nullifier_hash:
            raise DomainError(400, "nullifier_hash must not be empty")
        if not receipt_code:
            raise DomainError(400, "receipt_code must not be empty")
        if not sealed_vote_package_hash:
            raise DomainError(400, "sealed_vote_package_hash must not be empty")
        if validity_proof_hash == "":
            raise DomainError(400, "validity_proof_hash must not be empty when provided")

        computed_package_hash = compute_sealed_vote_package_hash(sealed_vote_package)
        if computed_package_hash != sealed_vote_package_hash:
            raise DomainError(400, "sealed_vote_package_hash does not match sealed_vote_package")

        election_id_hash = self.election_service.election_id_hash(election_id)
        if validity_proof is not None:
            self.verify_private_valid_vote_binding(
                election_id=election_id,
                election_id_hash=election_id_hash,
                commitment=commitment,
                nullifier_hash=nullifier_hash,
                validity_proof=validity_proof,
                zk_service=zk_service,
            )

        if self.repository.get_cast_ballot_by_nullifier(election_id, nullifier_hash):
            raise DomainError(409, "nullifier_hash has already been used in this election")

        ballot_id = self.repository.create_id("cast_ballot_v2")
        existing_ballots = self.repository.list_cast_ballots_v2(election_id)
        previous_receipt_chain_hash = (
            existing_ballots[-1].receipt_chain_hash
            if existing_ballots
            else RECEIPT_CHAIN_GENESIS_V2
        )
        receipt_chain_hash = create_abp_v2_receipt_chain_hash(
            previous_receipt_chain_hash=previous_receipt_chain_hash,
            election_id_hash=election_id_hash,
            ballot_id=ballot_id,
            commitment=commitment,
            receipt_code=receipt_code,
            status="cast",
        )

        ballot = CastBallotRecordV2(
            ballot_id=ballot_id,
            election_id_hash=election_id_hash,
            commitment=commitment,
            nullifier_hash=nullifier_hash,
            sealed_vote_package=sealed_vote_package,
            sealed_vote_package_hash=sealed_vote_package_hash,
            validity_proof_hash=validity_proof_hash,
            receipt_code=receipt_code,
            receipt_chain_hash=receipt_chain_hash,
            created_at=utc_now(),
        )
        return self.repository.save_cast_ballot_v2(election_id, ballot)

    def verify_private_valid_vote_binding(
        self,
        election_id: str,
        election_id_hash: str,
        commitment: str,
        nullifier_hash: str,
        validity_proof: PrivateValidVoteProofV1,
        zk_service: Any | None,
    ) -> None:
        if zk_service is None:
            raise DomainError(500, "ZK service is not configured")

        manifest = self.election_service.build_manifest_v2(election_id)
        signals = validity_proof.public_signals

        if signals.election_id_hash != election_id_hash:
            raise DomainError(400, "validity_proof election_id_hash does not match election")
        if signals.eligibility_root != manifest.eligibility_root:
            raise DomainError(400, "validity_proof eligibility_root does not match election")
        if signals.nullifier_hash != nullifier_hash:
            raise DomainError(400, "validity_proof nullifier_hash does not match cast request")
        if signals.commitment != commitment:
            raise DomainError(400, "validity_proof commitment does not match cast request")
        if signals.rule_hash is not None and signals.rule_hash != manifest.rule_hash:
            raise DomainError(400, "validity_proof rule_hash does not match election manifest")

        if not zk_service.verify_private_valid_vote(validity_proof):
            raise DomainError(400, "private valid vote proof verification failed")

    def cast_ballot_public_payload(self, ballot: CastBallotRecordV2) -> dict[str, Any]:
        payload = ballot.model_dump(mode="json")
        payload.pop("sealed_vote_package", None)
        return payload

    def bulletin_board_v2(self, election_id: str) -> dict[str, Any]:
        manifest = self.election_service.build_manifest_v2(election_id)
        board = self.repository.get_bulletin_board_v2(election_id)
        return {
            "election_id": election_id,
            "election_id_hash": manifest.election_id_hash,
            "manifest": manifest,
            "cast_ballots_public": board["cast_ballots_public"],
            "challenge_records": board["challenge_records"],
            "roots": None,
        }


def create_legacy_commitment(election_id: str, vote_vector: list[int], randomness: str) -> str:
    return hash_object(
        "verivote.legacy_commitment.v1",
        {
            "election_id": election_id,
            "vote_vector": vote_vector,
            "randomness": randomness,
        },
    )


def create_abp_v2_receipt_chain_hash(
    previous_receipt_chain_hash: str,
    election_id_hash: str,
    ballot_id: str,
    commitment: str,
    receipt_code: str,
    status: str,
) -> str:
    return hash_object(
        "verivote.receipt_chain.v2",
        {
            "previous_receipt_chain_hash": previous_receipt_chain_hash,
            "election_id_hash": election_id_hash,
            "ballot_id": ballot_id,
            "commitment": commitment,
            "receipt_code": receipt_code,
            "status": status,
        },
    )
