from collections import Counter

from app.models.abp import LegacyBallot, TallyResultItem
from app.repositories.memory import MemoryRepository
from app.services.election_service import ElectionService


class TallyService:
    def __init__(self, repository: MemoryRepository, election_service: ElectionService) -> None:
        self.repository = repository
        self.election_service = election_service

    def tally(self, election_id: str, ballots: list[LegacyBallot]) -> list[TallyResultItem]:
        candidates = self.election_service.list_candidates(election_id)
        counts = Counter(ballot.candidate_id for ballot in ballots)
        return [
            TallyResultItem(
                candidate_id=candidate.id,
                candidate_name=candidate.name,
                vote_count=counts[candidate.id],
            )
            for candidate in candidates
        ]

