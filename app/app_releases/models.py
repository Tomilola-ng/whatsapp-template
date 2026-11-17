from tortoise import fields, models

from app.app_releases.enums import AppPlatform
from app.base.utils import IDPrefix, PREFIXED_ID_MAX_LENGTH, make_id_default


class AppRelease(models.Model):
    id = fields.CharField(
        pk=True,
        max_length=PREFIXED_ID_MAX_LENGTH,
        default=make_id_default(IDPrefix.APP_RELEASE),
    )
    platform = fields.CharEnumField(AppPlatform, max_length=10)
    version_name = fields.CharField(max_length=32)
    build_number = fields.IntField()
    minimum_supported_version_name = fields.CharField(max_length=32)
    minimum_supported_build_number = fields.IntField()
    force_update = fields.BooleanField(default=False)
    update_title = fields.CharField(max_length=120)
    update_message = fields.TextField()
    store_url = fields.CharField(max_length=500)
    is_active = fields.BooleanField(default=True)
    published_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "app_releases"
        unique_together = (("platform", "build_number"),)
        indexes = [
            ("platform", "is_active", "published_at", "build_number"),
            ("published_at",),
        ]
