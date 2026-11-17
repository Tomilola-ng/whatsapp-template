"""Admin class-based views for app releases (plain CRUD; policy logic is in services)."""

from typing import Any

from app.app_releases.models import AppRelease
from app.app_releases.schemas import ReleaseCreate, ReleaseOut, ReleasePatch
from app.app_releases.services import validate_release_values
from app.base.http_errors import api_error
from app.base.views import CRUD_ACTIONS, ModelView, ViewContext


class AppReleaseAdminView(ModelView):
    """``/admin/app/releases`` — create, list, retrieve, patch (no delete; deactivate instead)."""

    model = AppRelease
    prefix = "/admin/app/releases"
    tags = ["Administration"]
    audience = ("admin",)
    actions = tuple(a for a in CRUD_ACTIONS if a != "destroy")
    label = "App release"
    permissions = {"*": "app_releases.manage"}

    create_schema = ReleaseCreate
    update_schema = ReleasePatch
    out_schema = ReleaseOut

    filter_fields = ("platform", "is_active", "published_at__isnull")
    ordering_fields = ("platform", "build_number", "published_at", "created_at")
    ordering = ("platform", "-build_number", "id")
    conflict_code = "release_build_exists"
    conflict_message = "A release already exists for this platform and build."
    audit = True

    async def validate(
        self, values: dict[str, Any], ctx: ViewContext, instance: AppRelease | None = None
    ) -> dict[str, Any]:
        if "store_url" in values and values["store_url"] is not None:
            values["store_url"] = str(values["store_url"])
        for key, value in values.items():
            if key != "published_at" and value is None:
                raise api_error(422, "invalid_release", f"{key} cannot be null.")
        merged = {
            field: getattr(instance, field) if instance else None
            for field in (
                "version_name",
                "minimum_supported_version_name",
                "minimum_supported_build_number",
                "build_number",
                "store_url",
            )
        }
        merged.update(values)
        validate_release_values(merged)
        return values
