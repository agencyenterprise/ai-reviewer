from typing import List, TypedDict

from lib.agents.citation_detector import CitationResponse
from lib.agents.claim_detector import ClaimResponse
from lib.agents.reference_extractor import BibliographyItem
from lib.agents.claim_substantiator import ClaimSubstantiationResultWithClaimIndex
from lib.services.file import FileDocument


class ClaimSubstantiatorState(TypedDict, total=False):
    file: FileDocument
    supporting_files: List[FileDocument]

    # Outputs
    chunks: List[str]
    references: List[BibliographyItem]
    claims_by_chunk: List[ClaimResponse]
    citations_by_chunk: List[CitationResponse]
    claim_substantiations_by_chunk: List[List[ClaimSubstantiationResultWithClaimIndex]]
