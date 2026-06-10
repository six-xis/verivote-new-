from fastapi import APIRouter, Request, status

from app.schemas.abp import (
    BulletinBoardResponseV2,
    CastBallotRequestV2,
    CastBallotResponseV2,
    LegacyCastBallotRequest,
    LegacyCastBallotResponse,
)

router = APIRouter(tags=["ballots"])


@router.post(
    "/elections/{election_id}/ballots/legacy-cast",
    response_model=LegacyCastBallotResponse,
    status_code=status.HTTP_201_CREATED,
)
def legacy_cast_ballot(
    election_id: str,
    payload: LegacyCastBallotRequest,
    request: Request,
) -> LegacyCastBallotResponse:
    ballot = request.app.state.services.ballots.legacy_cast(
        election_id=election_id,
        user_id=payload.user_id,
        candidate_id=payload.candidate_id,
    )
    return LegacyCastBallotResponse(
        ballot_id=ballot.id,
        receipt_code=ballot.receipt_code,
        commitment=ballot.commitment,
        receipt_chain_hash=ballot.receipt_chain_hash,
        message="Legacy/simple cast accepted. This is not the final private ABP cast API.",
        ballot=ballot,
    )


@router.post(
    "/elections/{election_id}/ballots/cast",
    response_model=CastBallotResponseV2,
    status_code=status.HTTP_201_CREATED,
)
def cast_ballot_v2(
    election_id: str,
    payload: CastBallotRequestV2,
    request: Request,
) -> CastBallotResponseV2:
    ballot = request.app.state.services.ballots.cast_v2(
        election_id=election_id,
        commitment=payload.commitment,
        nullifier_hash=payload.nullifier_hash,
        sealed_vote_package=payload.sealed_vote_package,
        sealed_vote_package_hash=payload.sealed_vote_package_hash,
        receipt_code=payload.receipt_code,
        validity_proof_hash=payload.validity_proof_hash,
        validity_proof=payload.validity_proof,
        zk_service=request.app.state.services.zk,
    )
    return CastBallotResponseV2(
        **request.app.state.services.ballots.cast_ballot_public_payload(ballot)
    )


@router.get(
    "/elections/{election_id}/bulletin-board",
    response_model=BulletinBoardResponseV2,
)
def get_bulletin_board_v2(
    election_id: str,
    request: Request,
) -> BulletinBoardResponseV2:
    return BulletinBoardResponseV2(
        **request.app.state.services.ballots.bulletin_board_v2(election_id)
    )
