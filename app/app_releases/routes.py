import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.app_releases import services as release_services
from app.base.http_errors import api_error
from app.base.rate_limit import limiter
from app.base.responses import success_response
from app.config.settings import settings

router = APIRouter(prefix="/app", tags=["App Updates"])


@router.get("/update-policy")
@limiter.limit(settings.RATE_LIMIT_UPDATE_POLICY)
async def get_update_policy(
    request: Request, platform: str, version: str, build: int
):
    return success_response(
        await release_services.update_policy(platform, version, build),
        "Update policy retrieved",
    )


@router.get("/legal")
async def get_legal_urls():
    return success_response(
        {
            "terms_url": settings.TERMS_URL,
            "privacy_url": settings.PRIVACY_URL,
        },
        "Legal URLs retrieved",
    )


@router.get("/events/stream")
async def events_stream(request: Request, platform: str, version: str, build: int):
    parsed = release_services.parse_platform(platform)
    release_services.validate_version(version)
    if build <= 0:
        raise api_error(422, "invalid_build_number", "Build number must be positive.")

    async def generate():
        sent: set[str] = set()
        while not await request.is_disconnected():
            release = await release_services.latest_release(parsed)
            if release and release.build_number > build and release.id not in sent:
                policy = await release_services.update_policy(
                    parsed.value, version, build
                )
                policy.pop("current_version", None)
                policy.pop("current_build", None)
                policy.pop("check_after_seconds", None)
                payload = json.dumps(policy, default=str, separators=(",", ":"))
                yield (
                    f"event: app_update\nid: {release.id}:{release.build_number}\n"
                    f"data: {payload}\n\n"
                )
                sent.add(release.id)
            else:
                yield ": keep-alive\n\n"
            await asyncio.sleep(25)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
