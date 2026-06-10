from fastapi import APIRouter, Request

from app.schemas.abp import AuditReportResponse

router = APIRouter(tags=["audit"])


@router.get("/elections/{election_id}/audit/report", response_model=AuditReportResponse)
def get_audit_report(election_id: str, request: Request) -> AuditReportResponse:
    report = request.app.state.services.audit.build_report(election_id)
    return AuditReportResponse(report=report)

