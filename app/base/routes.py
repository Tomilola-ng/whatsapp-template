"""Base Routes"""

from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    status,
    UploadFile,
    File,
    Form,
    Depends,
    Query,
)
from fastapi.security import HTTPBearer

from app.accounts.models import Account
from app.access.permissions import require_permission
from app.accounts.permissions import get_current_active_user
from app.base.schemas import FileOut
from app.base.services import upload_file_asset, list_file_assets
from app.config.settings import settings
from app.config.pagination import (
    PaginationParams,
    PaginatedResponse,
    get_pagination_params,
)

router = APIRouter(prefix="/base", tags=["Base"])
security = HTTPBearer()


@router.post(
    "/files",
    response_model=FileOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(security), Depends(require_permission("files.create"))],
)
async def upload_file(
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    folder: str = Form("files"),
    current_user: Annotated[Account, Depends(get_current_active_user)] = ...,
):
    """
    Upload an file to R2 storage and create an FileAsset record.

    - Accepts multipart form-data with `file` (UploadFile), optional `alt_text`, and optional `folder`.
    - Stores the file under `<folder>/<uuid>.<ext>` in R2.
    - Returns FileOut with a presigned preview URL (`url`).
    """
    _ = current_user
    file_asset = await upload_file_asset(file=file, folder=folder, alt_text=alt_text)
    return FileOut.model_validate(file_asset)


if settings.ENVIRONMENT == "local":
    @router.get(
        "/files",
        response_model=PaginatedResponse[FileOut],
        status_code=status.HTTP_200_OK,
        dependencies=[Depends(security), Depends(require_permission("files.read"))],
    )
    async def list_files(
        pagination_params: PaginationParams = Depends(get_pagination_params),
        folder: Optional[str] = Query(
            None, description="Filter by folder prefix, e.g., 'files'"
        ),
        current_user: Annotated[Account, Depends(get_current_active_user)] = ...,
    ):
        """
        List files with pagination. Each item includes a presigned `url` for preview.
        Optionally filter by `folder` (prefix).
        """
        _ = current_user
        return await list_file_assets(pagination_params=pagination_params, folder=folder)
