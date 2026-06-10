from fastapi import APIRouter, Request

router = APIRouter(tags=["tally"])


@router.get("/elections/{election_id}/tally")
def get_tally(election_id: str, request: Request) -> dict:
    report = request.app.state.services.audit.build_report(election_id)
    return {"election_id": election_id, "tally": report.tally, "tally_hash": report.tally_hash}


@router.get("/elections/{election_id}/result")
def get_result(election_id: str, request: Request) -> dict:
    report = request.app.state.services.audit.build_report(election_id)
    election = request.app.state.services.elections.public_election_detail(election_id)
    results = [
        {
            "candidateId": item.candidate_id,
            "candidateName": item.candidate_name,
            "voteCount": item.vote_count,
        }
        for item in report.tally
    ]
    return {
        "election": election,
        "result": {
            "electionId": election_id,
            "totalVotes": report.valid_ballots,
            "results": results,
        },
    }
