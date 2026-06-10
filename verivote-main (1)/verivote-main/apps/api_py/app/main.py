from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as v2_router
from app.api.v1.legacy import router as legacy_router
from app.core.config import get_settings
from app.core.errors import DomainError, domain_error_handler
from app.repositories.memory import MemoryRepository
from app.schemas.abp import StatusResponse
from app.services.attack_service import AttackService
from app.services.audit_service import AuditService
from app.services.ballot_service import BallotService
from app.services.blockchain_service import BlockchainService
from app.services.election_service import ElectionService
from app.services.eligibility_service import EligibilityService
from app.services.tally_service import TallyService
from app.services.zk_service import ZkService


def create_app() -> FastAPI:
    settings = get_settings()
    repository = MemoryRepository()
    election_service = ElectionService(repository)
    tally_service = TallyService(repository, election_service)

    services = SimpleNamespace(
        elections=election_service,
        eligibility=EligibilityService(repository, election_service, settings),
        ballots=BallotService(repository, election_service),
        tally=tally_service,
        audit=AuditService(repository, election_service, tally_service),
        zk=ZkService(settings),
        blockchain=BlockchainService(settings),
        attacks=AttackService(repository, election_service),
    )

    app = FastAPI(
        title="VeriVote Python API",
        version="0.1.0",
        description="FastAPI baseline for VeriVote-ABP development.",
    )
    app.state.settings = settings
    app.state.repository = repository
    app.state.services = services

    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=StatusResponse)
    def health(request: Request) -> StatusResponse:
        return StatusResponse(
            ok=True,
            service="verivote-api-py",
            mode=request.app.state.settings.app_mode,
        )

    app.include_router(legacy_router)
    app.include_router(v2_router)
    return app


app = create_app()

