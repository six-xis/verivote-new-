import secrets

from app.core.errors import DomainError
from app.crypto.hash_utils import hash_object
from app.crypto.receipt_chain import (
    ReceiptChainInput,
    create_receipt_chain_hash,
    hash_receipt_code,
)
from app.models.abp import AttackMutation, LegacyBallot
from app.repositories.memory import MemoryRepository
from app.services.ballot_service import create_legacy_commitment
from app.services.election_service import ElectionService, utc_now


class AttackService:
    def __init__(self, repository: MemoryRepository, election_service: ElectionService) -> None:
        self.repository = repository
        self.election_service = election_service

    def tamper_commitment(self, election_id: str) -> AttackMutation:
        self.election_service.require_election(election_id)
        ballot = self._first_ballot(election_id)
        before = {"ballot_id": ballot.id, "commitment": ballot.commitment}
        ballot.commitment = hash_object(
            "verivote.attack.tampered_commitment.v1",
            {"old_commitment": ballot.commitment},
        )
        self.repository.save_ballot(ballot)
        mutation = AttackMutation(
            id=self.repository.create_id("attack"),
            election_id=election_id,
            attack_type="tamper-commitment",
            before=before,
            after={"ballot_id": ballot.id, "commitment": ballot.commitment},
            created_at=utc_now(),
        )
        return self.repository.save_attack_mutation(mutation)

    def inject_duplicate(self, election_id: str) -> AttackMutation:
        self.election_service.require_election(election_id)
        source = self._first_ballot(election_id)
        ballots = sorted(
            self.repository.list_ballots(election_id),
            key=lambda ballot: ballot.receipt_chain_index,
        )
        previous = ballots[-1]
        previous_hash = hash_receipt_code(previous.receipt_code)
        receipt_chain_index = len(ballots)
        created_at = utc_now()
        randomness = secrets.token_hex(32)
        commitment = create_legacy_commitment(election_id, source.vote_vector, randomness)
        receipt_code = hash_object(
            "verivote.receipt_code.v1",
            {
                "election_id": election_id,
                "commitment": commitment,
                "user_id": source.user_id,
                "created_at": created_at,
            },
        )
        receipt_chain_hash = create_receipt_chain_hash(
            ReceiptChainInput(
                election_id=election_id,
                receipt_code=receipt_code,
                previous_receipt_code_hash=previous_hash,
                receipt_chain_index=receipt_chain_index,
                commitment=commitment,
            )
        )
        duplicate = LegacyBallot(
            id=self.repository.create_id("ballot"),
            election_id=election_id,
            user_id=source.user_id,
            candidate_id=source.candidate_id,
            vote_vector=source.vote_vector.copy(),
            randomness=randomness,
            commitment=commitment,
            receipt_code=receipt_code,
            previous_receipt_code_hash=previous_hash,
            receipt_chain_index=receipt_chain_index,
            receipt_chain_hash=receipt_chain_hash,
            created_at=created_at,
        )
        self.repository.save_ballot(duplicate)

        mutation = AttackMutation(
            id=self.repository.create_id("attack"),
            election_id=election_id,
            attack_type="inject-duplicate",
            before={"source_ballot_id": source.id, "user_id": source.user_id},
            after={"duplicate_ballot_id": duplicate.id, "user_id": duplicate.user_id},
            created_at=created_at,
        )
        return self.repository.save_attack_mutation(mutation)

    def _first_ballot(self, election_id: str) -> LegacyBallot:
        ballots = sorted(
            self.repository.list_ballots(election_id),
            key=lambda ballot: ballot.receipt_chain_index,
        )
        if not ballots:
            raise DomainError(409, "no ballot available for attack mutation")
        return ballots[0]

