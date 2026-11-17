"""Internal job routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.config.settings import settings
from app.schedules.jobs.maintenance import run_maintenance

router = APIRouter(prefix="/internal/jobs", tags=["Internal Jobs"])


def verify_internal_job_token(
    x_internal_token: Annotated[str | None, Header(alias="X-Internal-Token")] = None,
) -> None:
    """Protect internal job routes with a shared token outside local development."""
    if settings.ENVIRONMENT == "local" and not settings.INTERNAL_JOB_TOKEN:
        return
    if not settings.INTERNAL_JOB_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal job token is not configured.",
        )
    if x_internal_token != settings.INTERNAL_JOB_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal job token.",
        )


@router.post("/run-maintenance", dependencies=[Depends(verify_internal_job_token)])
async def run_maintenance_job():
    """Run starter maintenance jobs."""
    return {"message": "Maintenance complete", "data": await run_maintenance()}
