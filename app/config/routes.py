"""API router registration for supported starter modules."""

from fastapi import APIRouter

from app.access import routes as access_routes
from app.accounts import routes as accounts_routes
from app.app_releases import routes as app_release_routes
from app.app_releases.views import AppReleaseAdminView
from app.audit import routes as audit_routes
from app.base.rate_limit import limiter
from app.base import routes as base_routes
from app.base.utils import health_check
from app.contact import routes as contact_routes
from app.client_errors import routes as client_error_routes
from app.config.settings import settings
from app.integration import dev_outbox
from app.records import notification_routes, staff_routes
from app.schedules import routes as schedule_routes
from app.whatsapp import routes as whatsapp_routes


api_router = APIRouter()

api_router.include_router(accounts_routes.router)
api_router.include_router(access_routes.router)
api_router.include_router(base_routes.router)
api_router.include_router(contact_routes.router)
api_router.include_router(notification_routes.router)
api_router.include_router(staff_routes.router)
api_router.include_router(app_release_routes.router)
api_router.include_router(AppReleaseAdminView.as_router())
api_router.include_router(audit_routes.router)
api_router.include_router(client_error_routes.router)
api_router.include_router(schedule_routes.router)
api_router.include_router(whatsapp_routes.router)
if settings.ENVIRONMENT == "local" and settings.DEV_OUTBOX_ENABLED:
    api_router.include_router(dev_outbox.router)


@limiter.exempt
@api_router.get("/health")
def health():
    """Health check endpoint"""
    return health_check()
