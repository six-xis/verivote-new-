from fastapi import APIRouter, Request

router = APIRouter(prefix="/blockchain", tags=["blockchain"])


@router.get("/status")
def blockchain_status(request: Request) -> dict:
    return request.app.state.services.blockchain.status()

