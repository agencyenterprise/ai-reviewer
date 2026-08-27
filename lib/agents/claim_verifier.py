"""Shared vocabulary for describing how evidence backs a claim.

The verifier agent that once lived here was replaced by
`claim_reference_validation_v2`, which drives its own citation validator; only
these two types outlived it.
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class EvidenceAlignmentLevel(StrEnum):
    UNVERIFIABLE = "unverifiable"
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"


class ClaimEvidenceSource(BaseModel):
    quote: str = Field(
        description="A quote from the document that contains the evidence for the claim. If no quote was found, return an empty string."
    )
    location: str = Field(
        description="The location of the quote in the document, e.g., 'page 3', 'section 2', 'figure 3', etc. Be as specific as possible. Don't use line numbers, but rather section titles or other section identifiers. If no location was found, return an empty string."
    )
    file_id: str = Field(
        description="The ID of the reference file that was checked as provided in the citation-to-file mapping."
    )
