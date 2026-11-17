from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator

from app.app_releases.enums import AppPlatform


class ReleaseCreate(BaseModel):
    platform: AppPlatform
    version_name: str = Field(max_length=32)
    build_number: int = Field(gt=0)
    minimum_supported_version_name: str = Field(max_length=32)
    minimum_supported_build_number: int = Field(gt=0)
    force_update: bool = False
    update_title: str = Field(min_length=1, max_length=120)
    update_message: str = Field(min_length=1, max_length=1000)
    store_url: AnyHttpUrl
    is_active: bool = True
    published_at: datetime | None = None

    @model_validator(mode="after")
    def validate_builds(self):
        if self.minimum_supported_build_number > self.build_number:
            raise ValueError("minimum supported build cannot exceed release build")
        if self.store_url.scheme != "https":
            raise ValueError("store_url must use HTTPS")
        return self


class ReleasePatch(BaseModel):
    version_name: str | None = Field(default=None, max_length=32)
    minimum_supported_version_name: str | None = Field(default=None, max_length=32)
    minimum_supported_build_number: int | None = Field(default=None, gt=0)
    force_update: bool | None = None
    update_title: str | None = Field(default=None, min_length=1, max_length=120)
    update_message: str | None = Field(default=None, min_length=1, max_length=1000)
    store_url: AnyHttpUrl | None = None
    is_active: bool | None = None
    published_at: datetime | None = None


class ReleaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    platform: AppPlatform
    version_name: str
    build_number: int
    minimum_supported_version_name: str
    minimum_supported_build_number: int
    force_update: bool
    update_title: str
    update_message: str
    store_url: str
    is_active: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
