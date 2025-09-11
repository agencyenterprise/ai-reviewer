from typing import List
from pydantic import BaseModel

from lib.agents.citation_detector import CitationResponse
from lib.agents.claim_detector import ClaimResponse
from lib.agents.claim_substantiator import ClaimSubstantiationResult
from lib.agents.reference_extractor import BibliographyItem


# TODO: can probably be removed after we change the workflow to use pydantic model instead
class ClaimSubstantiatorOutputModel(BaseModel):
    claims_by_chunk: List[ClaimResponse]
    citations_by_chunk: List[CitationResponse]
    references: List[BibliographyItem]
    claim_substantiations_by_chunk: List[List[ClaimSubstantiationResult]]
