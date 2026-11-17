"""Wiring + behaviour tests for ``app.base.views`` (in-memory SQLite, auth overridden)."""

import unittest

import httpx
from fastapi import FastAPI
from tortoise import Tortoise

from app.accounts.models import Account
from app.access.permissions import TokenAuth, get_validated_token_auth
from app.app_releases.models import AppRelease
from app.app_releases.views import AppReleaseAdminView
from app.base.views import ModelView, ReadOnlyModelView, ViewContext, action
from app.config.settings import settings

RELEASE = {
    "platform": "IOS",
    "version_name": "1.0.0",
    "build_number": 10,
    "minimum_supported_version_name": "1.0.0",
    "minimum_supported_build_number": 5,
    "update_title": "Update",
    "update_message": "Please update",
    "store_url": "https://apps.example.com/app",
}


class PublicReleaseView(ReadOnlyModelView):
    model = AppRelease
    prefix = "/public/releases"
    tags = ["Test"]
    public_actions = ("list", "retrieve")
    search_fields = ("version_name",)
    ordering_fields = ("build_number",)
    filter_fields = ("platform", "build_number__gte")


class ActionReleaseView(ModelView):
    model = AppRelease
    prefix = "/action/releases"
    tags = ["Test"]
    actions = ("retrieve",)
    soft_delete_field = "is_active"
    permissions = {"*": "app_releases.manage"}

    @action(detail=True, methods=("POST",), path="deactivate")
    async def deactivate(self, id: str, ctx: ViewContext):
        obj = await self.get_object(ctx, id)
        await self.perform_destroy(obj, ctx)
        return {"id": obj.id, "is_active": obj.is_active}


class AutoSchemaView(ModelView):
    """No schemas declared: out/create/update are generated from the model."""

    model = AppRelease
    prefix = "/auto/releases"
    tags = ["Test"]
    public_actions = ("list", "retrieve", "create", "partial_update", "destroy")


def _auth(account_id: str, perms: tuple[str, ...]) -> TokenAuth:
    return TokenAuth(account_id, "admin", perms, 0, 0)


class ModelViewTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": settings.tortoise_models},
        )
        await Tortoise.generate_schemas()
        app = FastAPI()
        for view in (AppReleaseAdminView, PublicReleaseView, ActionReleaseView, AutoSchemaView):
            app.include_router(view.as_router())
        self.account = await Account.create(email="staff@example.com")
        self.perms: tuple[str, ...] = ("*",)
        app.dependency_overrides[get_validated_token_auth] = lambda: _auth(
            self.account.id, self.perms
        )
        self.app = app
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        await Tortoise.close_connections()

    async def test_admin_crud_envelope_and_conflict(self) -> None:
        base = "/admin/app/releases"
        created = await self.client.post(base, json=RELEASE)
        self.assertEqual(created.status_code, 201, created.text)
        body = created.json()
        self.assertTrue(body["success"])
        rid = body["data"]["id"]
        self.assertTrue(rid.startswith("REL_"))

        dup = await self.client.post(base, json=RELEASE)
        self.assertEqual(dup.status_code, 409)
        self.assertEqual(dup.json()["detail"]["code"], "release_build_exists")

        patched = await self.client.patch(f"{base}/{rid}", json={"update_title": "New"})
        self.assertEqual(patched.json()["data"]["update_title"], "New")

        bad = await self.client.patch(f"{base}/{rid}", json={"minimum_supported_build_number": 99})
        self.assertEqual(bad.status_code, 422)

        listing = await self.client.get(base, params={"platform": "IOS", "is_active": "true"})
        data = listing.json()["data"]
        self.assertEqual(data["meta"]["total_items"], 1)
        self.assertEqual(data["items"][0]["id"], rid)

        self.assertEqual((await self.client.get(f"{base}/REL_missing")).status_code, 404)
        self.assertEqual((await self.client.delete(f"{base}/{rid}")).status_code, 405)

        from app.audit.models import AuditLog

        logs = await AuditLog.filter(entity_id=rid).order_by("created_at")
        self.assertEqual([log.action for log in logs], ["app_release.create", "app_release.update"])
        self.assertEqual(logs[0].actor_account_id, self.account.id)

    async def test_permission_denied(self) -> None:
        self.perms = ("files.read",)
        response = await self.client.get("/admin/app/releases")
        self.assertEqual(response.status_code, 403)

    async def test_public_read_only_search_filter_order(self) -> None:
        await AppRelease.create(**{**RELEASE, "platform": "IOS", "build_number": 1,
                                   "version_name": "1.0.0", "minimum_supported_build_number": 1})
        await AppRelease.create(**{**RELEASE, "platform": "ANDROID", "build_number": 2,
                                   "version_name": "2.0.0", "minimum_supported_build_number": 1})
        self.perms = ()
        listing = await self.client.get("/public/releases", params={"q": "2.0", "ordering": "-build_number"})
        self.assertEqual([i["version_name"] for i in listing.json()["data"]["items"]], ["2.0.0"])
        gte = await self.client.get("/public/releases", params={"build_number__gte": 2})
        self.assertEqual(gte.json()["data"]["meta"]["total_items"], 1)
        bad_order = await self.client.get("/public/releases", params={"ordering": "store_url"})
        self.assertEqual(bad_order.status_code, 422)
        self.assertEqual((await self.client.post("/public/releases", json=RELEASE)).status_code, 405)

    async def test_custom_action_and_soft_delete(self) -> None:
        row = await AppRelease.create(**{**RELEASE, "minimum_supported_build_number": 1})
        response = await self.client.post(f"/action/releases/{row.id}/deactivate")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["data"], {"id": row.id, "is_active": False})
        self.assertFalse((await AppRelease.get(id=row.id)).is_active)

    async def test_generated_schemas_full_crud(self) -> None:
        created = await self.client.post("/auto/releases", json=RELEASE)
        self.assertEqual(created.status_code, 201, created.text)
        rid = created.json()["data"]["id"]
        patched = await self.client.patch(f"/auto/releases/{rid}", json={"force_update": True})
        self.assertTrue(patched.json()["data"]["force_update"])
        self.assertEqual((await self.client.delete(f"/auto/releases/{rid}")).status_code, 200)
        self.assertEqual((await self.client.get(f"/auto/releases/{rid}")).status_code, 404)

    async def test_openapi_audience_and_schemas(self) -> None:
        from app.base.openapi import attach_dual_openapi

        attach_dual_openapi(self.app)
        admin = self.app.openapi_admin()  # type: ignore[attr-defined]
        public = self.app.openapi_app()  # type: ignore[attr-defined]
        self.assertIn("/admin/app/releases", admin["paths"])
        self.assertNotIn("/admin/app/releases", public["paths"])
        list_op = admin["paths"]["/admin/app/releases"]["get"]
        names = {p["name"] for p in list_op["parameters"]}
        self.assertTrue({"platform", "is_active", "page", "page_size", "ordering"} <= names)
        self.assertEqual(list_op["security"], [{"BearerAuth": []}])
        self.assertEqual(public["paths"]["/public/releases"]["get"]["security"], [])


if __name__ == "__main__":
    unittest.main()
