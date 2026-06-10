from app.crypto.hash_utils import hash_object
from app.crypto.merkle import merkle_root
from app.crypto.receipt_chain import verify_receipt_chain
from app.models.abp import AuditReport, LegacyBallot, ReceiptChainBreak
from app.repositories.memory import MemoryRepository
from app.services.ballot_service import create_legacy_commitment
from app.services.election_service import ElectionService, utc_now
from app.services.tally_service import TallyService


class AuditService:
    def __init__(
        self,
        repository: MemoryRepository,
        election_service: ElectionService,
        tally_service: TallyService,
    ) -> None:
        self.repository = repository
        self.election_service = election_service
        self.tally_service = tally_service

    def build_report(self, election_id: str) -> AuditReport:
        self.election_service.require_election(election_id)
        ballots = self.repository.list_ballots(election_id)
        candidate_ids = {candidate.id for candidate in self.election_service.list_candidates(election_id)}

        seen_users: set[str] = set()
        duplicate_ballot_ids: set[str] = set()
        invalid_ballot_ids: set[str] = set()
        for ballot in ballots:
            if ballot.user_id in seen_users:
                duplicate_ballot_ids.add(ballot.id)
            else:
                seen_users.add(ballot.user_id)
            if ballot.candidate_id not in candidate_ids:
                invalid_ballot_ids.add(ballot.id)

        commitment_failures = [
            ballot.id
            for ballot in ballots
            if ballot.commitment
            != create_legacy_commitment(ballot.election_id, ballot.vote_vector, ballot.randomness)
        ]
        commitment_openings_verified = not commitment_failures

        chain_result = verify_receipt_chain(ballots)
        valid_ballots = [
            ballot
            for ballot in ballots
            if ballot.id not in duplicate_ballot_ids and ballot.id not in invalid_ballot_ids
        ]
        tally = self.tally_service.tally(election_id, valid_ballots)

        commitment_root = merkle_root([ballot.commitment for ballot in valid_ballots])
        nullifier_root = merkle_root(
            [
                hash_object(
                    "verivote.legacy_nullifier_placeholder.v1",
                    {"election_id": election_id, "user_id": ballot.user_id},
                )
                for ballot in valid_ballots
            ]
        )
        receipt_root = merkle_root([ballot.receipt_chain_hash for ballot in valid_ballots])
        tally_hash = hash_object(
            "verivote.legacy_tally.v1",
            {"election_id": election_id, "tally": [item.model_dump() for item in tally]},
        )
        audit_bundle_hash = hash_object(
            "verivote.legacy_audit_bundle.v1",
            {
                "election_id": election_id,
                "commitment_root": commitment_root,
                "nullifier_root": nullifier_root,
                "receipt_root": receipt_root,
                "tally_hash": tally_hash,
                "total_ballots": len(ballots),
            },
        )
        status = (
            "passed"
            if chain_result.verified
            and commitment_openings_verified
            and not duplicate_ballot_ids
            and not invalid_ballot_ids
            else "failed"
        )

        report = AuditReport(
            election_id=election_id,
            total_ballots=len(ballots),
            valid_ballots=len(valid_ballots),
            invalid_ballots=len(invalid_ballot_ids),
            duplicate_ballots=len(duplicate_ballot_ids),
            receipt_chain_verified=chain_result.verified,
            receipt_chain_breaks=[
                ReceiptChainBreak(
                    ballot_id=item.ballot_id,
                    index=item.index,
                    reason=item.reason,
                )
                for item in chain_result.breaks
            ],
            commitment_openings_verified=commitment_openings_verified,
            commitment_opening_failures=commitment_failures,
            commitment_root=commitment_root,
            nullifier_root=nullifier_root,
            receipt_root=receipt_root,
            tally_hash=tally_hash,
            audit_bundle_hash=audit_bundle_hash,
            tally=tally,
            status=status,
            created_at=utc_now(),
        )
        return self.repository.save_audit_report(report)


def last_ballot(ballots: list[LegacyBallot]) -> LegacyBallot | None:
    if not ballots:
        return None
    return max(ballots, key=lambda ballot: ballot.receipt_chain_index)

