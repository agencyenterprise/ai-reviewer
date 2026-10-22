"""Which Draft Detective user a Microsoft account is, by its email.

The web app knows a person by email: whichever provider they sign in with, the session's
email finds or creates their ``users`` row (``lib/api/auth.py``). The Word add-in and the
Teams bot know them as a Microsoft account. Matching that account to a user by the same
email lists a conversation in the pane or in Teams under that user, and answers it with
the OpenAI key that user saved, as /chat does.

That is no more than the web app already grants the same account: signing in there with
Microsoft, the same ``email`` claim from the same tenant opens that user, saved key and
all. What a person may do with documents and handoffs in the add-in or in Teams is still
decided by their object id (``lib/api/addin_auth.py``, Teams handoffs), never by this.

Two conditions, both needed for the email to mean the same person:

- **The email claim itself, as the web app reads it.** Its Microsoft sign-in takes the
  profile's ``email``. Falling back to the UPN, which can differ from it, would make a
  second user rather than find the first, so an account without one stays unlinked.
- **One configured tenant.** Entra does not verify the ``email`` claim: an admin can set
  any address on their tenant's accounts. Draft Detective's Microsoft sign-in naming one
  tenant (``AUTH_MICROSOFT_ENTRA_ID_ISSUER``) is what makes an email from that tenant
  trustworthy, as it already is for the web app. With a multi-tenant issuer, or an
  account from another tenant, nothing is linked.
"""

import logging
import re
import uuid

from lib.config.env import config
from lib.services.users import get_or_create_user_by_email

logger = logging.getLogger(__name__)

_TENANT_ISSUER = re.compile(
    r"^https://login\.microsoftonline\.com/(?P<tenant>[0-9a-f-]{36})/v2\.0/?$",
    re.IGNORECASE,
)


def configured_tenant() -> str | None:
    """The one tenant Draft Detective's Microsoft sign-in accepts, if it names one."""

    issuer = (config.AUTH_MICROSOFT_ENTRA_ID_ISSUER or "").strip()
    match = _TENANT_ISSUER.match(issuer)
    return match.group("tenant").lower() if match else None


async def user_for(
    email: str | None, name: str | None, tenant: str | None
) -> uuid.UUID | None:
    """The user a Microsoft account signing in with ``email`` is, created if new.

    None when the email cannot be trusted to mean that user: see the module docstring.
    """

    allowed = configured_tenant()
    if not email or not allowed or not tenant or tenant.lower() != allowed:
        return None
    try:
        user = await get_or_create_user_by_email(email=email, name=name or email)
    except Exception:  # noqa: BLE001 - listing is optional; the conversation is not
        logger.warning("could not link a Microsoft account to a user", exc_info=True)
        return None
    return user.id
