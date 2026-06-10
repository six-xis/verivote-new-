from fastapi import APIRouter, Request, status

from app.schemas.abp import (
    DemoCredentialIssuePayload,
    DemoCredentialResponse,
    DemoRegisterRequest,
    DeriveNullifierRequestV2,
    DeriveNullifierResponseV2,
    PublicCredentialsResponseV2,
)

router = APIRouter(tags=["credentials"])


@router.post(
    "/elections/{election_id}/users/demo-register",
    response_model=DemoCredentialResponse,
    status_code=status.HTTP_201_CREATED,
)
def demo_register(
    election_id: str,
    payload: DemoRegisterRequest,
    request: Request,
) -> DemoCredentialResponse:
    credential = request.app.state.services.eligibility.demo_register(
        election_id=election_id,
        user_id=payload.user_id,
    )
    return DemoCredentialResponse(
        credential=credential,
        message="Demo credential registered. This is not production eligibility.",
    )


@router.post(
    "/elections/{election_id}/credentials/demo-issue",
    response_model=DemoCredentialIssuePayload,
    status_code=status.HTTP_201_CREATED,
)
def demo_issue_credential(
    election_id: str,
    request: Request,
) -> DemoCredentialIssuePayload:
    return request.app.state.services.eligibility.issue_demo_credential(election_id)


@router.get(
    "/elections/{election_id}/credentials/public",
    response_model=PublicCredentialsResponseV2,
)
def list_public_credentials(
    election_id: str,
    request: Request,
) -> PublicCredentialsResponseV2:
    eligibility = request.app.state.services.eligibility
    return PublicCredentialsResponseV2(
        eligibility_root=eligibility.get_eligibility_root(election_id),
        credentials=eligibility.list_public_credentials(election_id),
    )


@router.post(
    "/elections/{election_id}/credentials/derive-nullifier",
    response_model=DeriveNullifierResponseV2,
)
def derive_nullifier(
    election_id: str,
    payload: DeriveNullifierRequestV2,
    request: Request,
) -> DeriveNullifierResponseV2:
    return DeriveNullifierResponseV2(
        nullifier_hash=request.app.state.services.eligibility.derive_nullifier_for_demo(
            election_id=election_id,
            credential_secret=payload.credential_secret,
        ),
        warning=(
            "demo/dev helper only; production clients should derive the nullifier locally "
            "without sending the credential secret to the backend"
        ),
    )
