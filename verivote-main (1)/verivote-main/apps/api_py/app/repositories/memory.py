from collections import defaultdict

from app.models.abp import (
    AttackMutation,
    AuditReport,
    Candidate,
    CastBallotRecordV2,
    ChallengeBallotRecordV2,
    DemoCredential,
    DemoCredentialRecordV2,
    Election,
    LegacyBallot,
)


class MemoryRepository:
    def __init__(self) -> None:
        self.elections: dict[str, Election] = {}
        self.candidates: dict[str, Candidate] = {}
        self.credentials: dict[str, DemoCredential] = {}
        self.demo_credentials_v2: dict[str, DemoCredentialRecordV2] = {}
        self.demo_credential_v2_elections: dict[str, str] = {}
        self.ballots: dict[str, LegacyBallot] = {}
        self.cast_ballots_v2: dict[str, CastBallotRecordV2] = {}
        self.cast_ballot_v2_elections: dict[str, str] = {}
        self.challenge_ballots_v2: dict[str, list[ChallengeBallotRecordV2]] = defaultdict(list)
        self.audit_reports: dict[str, AuditReport] = {}
        self.attack_mutations: list[AttackMutation] = []
        self._counters: defaultdict[str, int] = defaultdict(int)

    def create_id(self, prefix: str) -> str:
        self._counters[prefix] += 1
        return f"{prefix}_{self._counters[prefix]}"

    def save_election(self, election: Election) -> Election:
        self.elections[election.id] = election
        return election

    def get_election(self, election_id: str) -> Election | None:
        return self.elections.get(election_id)

    def save_candidate(self, candidate: Candidate) -> Candidate:
        self.candidates[candidate.id] = candidate
        return candidate

    def get_candidate(self, candidate_id: str) -> Candidate | None:
        return self.candidates.get(candidate_id)

    def list_candidates(self, election_id: str) -> list[Candidate]:
        return [
            candidate
            for candidate in self.candidates.values()
            if candidate.election_id == election_id
        ]

    def save_credential(self, credential: DemoCredential) -> DemoCredential:
        self.credentials[f"{credential.election_id}:{credential.user_id}"] = credential
        return credential

    def get_credential(self, election_id: str, user_id: str) -> DemoCredential | None:
        return self.credentials.get(f"{election_id}:{user_id}")

    def save_demo_credential(
        self,
        election_id: str,
        credential_record: DemoCredentialRecordV2,
    ) -> DemoCredentialRecordV2:
        self.demo_credentials_v2[credential_record.credential_id] = credential_record
        self.demo_credential_v2_elections[credential_record.credential_id] = election_id
        return credential_record

    def list_demo_credentials(self, election_id: str) -> list[DemoCredentialRecordV2]:
        return [
            credential
            for credential_id, credential in self.demo_credentials_v2.items()
            if self.demo_credential_v2_elections.get(credential_id) == election_id
        ]

    def get_demo_credential_by_id(
        self,
        election_id: str,
        credential_id: str,
    ) -> DemoCredentialRecordV2 | None:
        credential = self.demo_credentials_v2.get(credential_id)
        if (
            credential is None
            or self.demo_credential_v2_elections.get(credential_id) != election_id
        ):
            return None
        return credential

    def update_election_eligibility_root(
        self,
        election_id: str,
        eligibility_root: str,
    ) -> Election | None:
        election = self.elections.get(election_id)
        if election is None:
            return None
        election.eligibility_root = eligibility_root
        self.elections[election_id] = election
        return election

    def save_ballot(self, ballot: LegacyBallot) -> LegacyBallot:
        self.ballots[ballot.id] = ballot
        return ballot

    def get_ballot(self, ballot_id: str) -> LegacyBallot | None:
        return self.ballots.get(ballot_id)

    def list_ballots(self, election_id: str) -> list[LegacyBallot]:
        return [
            ballot
            for ballot in self.ballots.values()
            if ballot.election_id == election_id
        ]

    def save_cast_ballot_v2(
        self,
        election_id: str,
        ballot: CastBallotRecordV2,
    ) -> CastBallotRecordV2:
        self.cast_ballots_v2[ballot.ballot_id] = ballot
        self.cast_ballot_v2_elections[ballot.ballot_id] = election_id
        return ballot

    def list_cast_ballots_v2(self, election_id: str) -> list[CastBallotRecordV2]:
        return [
            ballot
            for ballot_id, ballot in self.cast_ballots_v2.items()
            if self.cast_ballot_v2_elections.get(ballot_id) == election_id
        ]

    def get_cast_ballot_by_nullifier(
        self,
        election_id: str,
        nullifier_hash: str,
    ) -> CastBallotRecordV2 | None:
        for ballot in self.list_cast_ballots_v2(election_id):
            if ballot.nullifier_hash == nullifier_hash:
                return ballot
        return None

    def list_challenge_ballots_v2(self, election_id: str) -> list[ChallengeBallotRecordV2]:
        return list(self.challenge_ballots_v2[election_id])

    def get_bulletin_board_v2(self, election_id: str) -> dict[str, list]:
        public_cast_ballots = []
        for ballot in self.list_cast_ballots_v2(election_id):
            public_ballot = ballot.model_dump(mode="json")
            public_ballot.pop("sealed_vote_package", None)
            public_cast_ballots.append(public_ballot)

        return {
            "cast_ballots_public": public_cast_ballots,
            "challenge_records": self.list_challenge_ballots_v2(election_id),
        }

    def save_audit_report(self, report: AuditReport) -> AuditReport:
        self.audit_reports[report.election_id] = report
        return report

    def get_audit_report(self, election_id: str) -> AuditReport | None:
        return self.audit_reports.get(election_id)

    def save_attack_mutation(self, mutation: AttackMutation) -> AttackMutation:
        self.attack_mutations.append(mutation)
        return mutation
