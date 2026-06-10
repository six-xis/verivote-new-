from app.core.config import Settings
from app.core.security import ensure_demo_credential_issuer_allowed
from app.crypto.eligibility import (
    build_eligibility_root,
    create_eligibility_merkle_proof,
    derive_credential_commitment,
    derive_nullifier_hash,
    generate_credential_secret,
)
from app.crypto.hash_utils import hash_object
from app.crypto.merkle import EMPTY_ROOT
from app.models.abp import CredentialV2, DemoCredential, DemoCredentialIssueResponse
from app.models.abp import DemoCredentialRecordV2
from app.repositories.memory import MemoryRepository
from app.services.election_service import ElectionService, utc_now


class EligibilityService:
    def __init__(
        self,
        repository: MemoryRepository,
        election_service: ElectionService,
        settings: Settings,
    ) -> None:
        self.repository = repository
        self.election_service = election_service
        self.settings = settings

    def demo_register(self, election_id: str, user_id: str) -> DemoCredential:
        ensure_demo_credential_issuer_allowed(self.settings)
        self.election_service.require_election(election_id)
        user_id = user_id.strip()

        existing = self.repository.get_credential(election_id, user_id)
        if existing is not None:
            return existing

        commitment = hash_object(
            "verivote.demo_credential_commitment.v1",
            {"election_id": election_id, "user_id": user_id},
        )
        credential = DemoCredential(
            id=self.repository.create_id("credential"),
            election_id=election_id,
            user_id=user_id,
            credential_commitment=commitment,
            created_at=utc_now(),
        )
        return self.repository.save_credential(credential)

    def issue_demo_credential(self, election_id: str) -> DemoCredentialIssueResponse:
        ensure_demo_credential_issuer_allowed(self.settings)
        self.election_service.require_election(election_id)

        credential_secret = generate_credential_secret()
        credential_commitment = derive_credential_commitment(credential_secret)
        credential_record = DemoCredentialRecordV2(
            credential_id=self.repository.create_id("credential_v2"),
            election_id=election_id,
            credential_secret=credential_secret,
            credential_commitment=credential_commitment,
            issued_at=utc_now(),
        )
        self.repository.save_demo_credential(election_id, credential_record)
        eligibility_root = self._recompute_and_store_eligibility_root(election_id)

        return DemoCredentialIssueResponse(
            credential_id=credential_record.credential_id,
            credential_secret=credential_secret,
            credential_commitment=credential_commitment,
            eligibility_root=eligibility_root,
            warning=(
                "demo only credential secret; do not publish; not for production "
                "eligibility issuance"
            ),
        )

    def list_public_credentials(self, election_id: str) -> list[CredentialV2]:
        self.election_service.require_election(election_id)
        credentials = self.repository.list_demo_credentials(election_id)
        commitments = [credential.credential_commitment for credential in credentials]
        return [
            CredentialV2(
                credential_id=credential.credential_id,
                credential_commitment=credential.credential_commitment,
                eligibility_merkle_path=create_eligibility_merkle_proof(
                    commitments,
                    credential.credential_commitment,
                ),
            )
            for credential in credentials
        ]

    def get_eligibility_root(self, election_id: str) -> str:
        election = self.election_service.require_election(election_id)
        return election.eligibility_root or EMPTY_ROOT

    def derive_nullifier_for_demo(self, election_id: str, credential_secret: str) -> str:
        election_id_hash = self.election_service.election_id_hash(election_id)
        return derive_nullifier_hash(election_id_hash, credential_secret)

    def _recompute_and_store_eligibility_root(self, election_id: str) -> str:
        commitments = [
            credential.credential_commitment
            for credential in self.repository.list_demo_credentials(election_id)
        ]
        eligibility_root = build_eligibility_root(commitments)
        self.repository.update_election_eligibility_root(election_id, eligibility_root)
        return eligibility_root
