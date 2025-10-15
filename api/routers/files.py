import mimetypes
import os

from fastapi import APIRouter
from starlette.responses import FileResponse

from lib.config.env import config

router = APIRouter(tags=["files"])


@router.get("/api/files/download/{xxhash}/{filename}")
async def download_file(xxhash: str, filename: str):
    """Download a file (forces download)"""

    file_path = os.path.join(config.FILE_UPLOADS_MOUNT_PATH, xxhash)
    media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return FileResponse(path=file_path, media_type=media_type)
