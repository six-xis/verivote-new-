from datetime import UTC, datetime

from app.core.errors import DomainError
from app.crypto.hash_utils import hash_object
from app.crypto.merkle import EMPTY_ROOT
from app.models.abp import Candidate, CandidateV2, Election, ElectionManifestV2
from app.repositories.memory import MemoryRepository


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class ElectionService:
    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository

    def create_election(self, title: str, description: str = "") -> Election:
        title = title.strip()
        if not title:
            raise DomainError(400, "title must not be empty")

        election = Election(
            id=self.repository.create_id("election"),
            title=title,
            description=description.strip(),
            eligibility_root=EMPTY_ROOT,
            created_at=utc_now(),
        )
        return self.repository.save_election(election)

    def require_election(self, election_id: str) -> Election:
        election = self.repository.get_election(election_id)
        if election is None:
            raise DomainError(404, "election not found")
        return election

    def election_id_hash(self, election_id: str) -> str:
        self.require_election(election_id)
        return hash_object("verivote.election_id.v2", {"election_id": election_id})

    def add_candidate(self, election_id: str, name: str, description: str = "") -> Candidate:
        self.require_election(election_id)
        name = name.strip()
        if not name:
            raise DomainError(400, "candidate name must not be empty")

        candidate = Candidate(
            id=self.repository.create_id("candidate"),
            election_id=election_id,
            name=name,
            description=description.strip(),
        )
        return self.repository.save_candidate(candidate)

    def require_candidate_for_election(self, election_id: str, candidate_id: str) -> Candidate:
        candidate = self.repository.get_candidate(candidate_id)
        if candidate is None or candidate.election_id != election_id:
            raise DomainError(404, "candidate not found for election")
        return candidate

    def list_candidates(self, election_id: str) -> list[Candidate]:
        self.require_election(election_id)
        return self.repository.list_candidates(election_id)

    def build_manifest_v2(self, election_id: str) -> ElectionManifestV2:
        election = self.require_election(election_id)
        candidates = [
            CandidateV2(
                candidate_id=candidate.id,
                name=candidate.name,
                description=candidate.description or None,
                index=index,
            )
            for index, candidate in enumerate(self.repository.list_candidates(election_id))
        ]
        return ElectionManifestV2(
            election_id=election.id,
            election_id_hash=self.election_id_hash(election_id),
            title=election.title,
            description=election.description or None,
            candidates=candidates,
            candidate_count=len(candidates),
            rule_hash=hash_object(
                "verivote.rules.default.v2",
                {
                    "election_id": election.id,
                    "candidate_count": len(candidates),
                    "one_hot_vote": True,
                },
            ),
            eligibility_root=election.eligibility_root or EMPTY_ROOT,
            tally_public_key=None,
            generator_context_hash=hash_object(
                "verivote.generator_context.v2",
                {"version": "phase3-reference"},
            ),
            created_at=election.created_at,
        )
