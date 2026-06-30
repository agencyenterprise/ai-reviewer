"""Public endpoint serving the About-page markdown content.

The content lives in the committed ABOUT.md at the repository root; deployments
customise the About page by editing that file in their fork.
"""

import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from lib.services.about_page import read_about_content

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/about", tags=["about"])


class AboutContentResponse(BaseModel):
    value: str


@router.get("", response_model=AboutContentResponse)
async def get_about_content() -> AboutContentResponse:
    """Return the About page markdown content (from the committed ABOUT.md)."""
    try:
        return AboutContentResponse(value=read_about_content())
    except OSError as e:
        logger.error("Failed to read ABOUT.md: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="About page content is unavailable.",
        )
