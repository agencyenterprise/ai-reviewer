"""Everything Draft Detective does inside Microsoft 365, under one prefix.

``/teams`` answers questions about a document the service loads itself, and writes
nothing: a server-side write is refused with 423 while anyone has the document open,
so changing a document belongs to a Word client rather than to this path.

The prefix is shared rather than per-product because the surfaces here share a
tenant, an identity model and a set of documents, and a caller reasoning about
permissions wants to see them together.
"""

from fastapi import APIRouter

from lib.api.routers.microsoft import teams

router = APIRouter(prefix="/api/microsoft")
router.include_router(teams.router)
