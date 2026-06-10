from fastapi import APIRouter, Request

router = APIRouter(tags=["tally"])


@router.get("/elections/{election_id}/tally")
def get_tally(election_id: str, request: Request) -> dict:
    report = request.app.state.services.audit.build_report(election_id)
    return {"election_id": election_id, "tally": report.tally, "tally_hash": report.tally_hash}

