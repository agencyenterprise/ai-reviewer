from typing import List, TypedDict
from pydantic import BaseModel

from lib.agents.citation_detector import CitationResponse
from lib.agents.claim_detector import ClaimResponse
from lib.agents.toulmin_claim_detector import ToulminClaimResponse
from lib.agents.reference_extractor import BibliographyItem
from lib.agents.claim_substantiator import ClaimSubstantiationResultWithClaimIndex
from lib.services.file import FileDocument


class ClaimSubstantiationChunk(BaseModel):
    """
    Wrapper for a list of claim substantiation results for a single chunk.

    openapi-generator does not support List[List[T]] so we need to wrap the list of substantiations in a single model.
    """

    substantiations: List[ClaimSubstantiationResultWithClaimIndex]


class ClaimSubstantiatorState(TypedDict, total=False):
    file: FileDocument
    supporting_files: List[FileDocument]

    # Outputs
    chunks: List[str]
    references: List[BibliographyItem]
    claims_by_chunk: List[ClaimResponse | ToulminClaimResponse]
    citations_by_chunk: List[CitationResponse]
    claim_substantiations_by_chunk: List[ClaimSubstantiationChunk]
