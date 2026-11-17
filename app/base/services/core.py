"""Base domain service-layer functions."""

from typing import Optional

from fastapi import UploadFile

from app.base.models import FileAsset
from app.base.schemas import FileOut
from app.config.pagination import (
    PaginationHelper,
    PaginationParams,
    PaginatedResponse,
)
from app.config.storage import r2_storage


async def upload_file_asset(
    file: UploadFile, folder: str = "files", alt_text: Optional[str] = None
) -> FileAsset:
    """Upload file to storage and persist a FileAsset record."""
    key = await r2_storage.upload_file(file=file, folder=folder)

    try:
        content = await file.read()
        file_size = len(content) if content is not None else None
    finally:
        await file.seek(0)

    return await FileAsset.create(
        key=key,
        alt_text=alt_text,
        content_type=file.content_type,
        file_size=file_size,
    )


async def list_file_assets(
    pagination_params: PaginationParams, folder: Optional[str] = None
) -> PaginatedResponse[FileOut]:
    """Paginate file assets with optional folder key-prefix filtering."""
    queryset = FileAsset.all().order_by("-id")
    if folder:
        prefix = folder if folder.endswith("/") else f"{folder}/"
        queryset = queryset.filter(key__startswith=prefix)

    items, meta = await PaginationHelper.paginate_queryset(queryset, pagination_params)
    out_items = [FileOut.model_validate(item) for item in items]
    return PaginationHelper.create_paginated_response(out_items, meta)
