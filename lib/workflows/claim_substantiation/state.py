from typing import List, TypedDict

from lib.agents.citation_detector import CitationResponse
from lib.agents.claim_detector import ClaimResponse
from lib.agents.reference_matcher import ReferenceMatch
from lib.services.file import File


class ClaimSubstantiatorState(TypedDict, total=False):
    file: File
    supporting_files: List[File]

    # Outputs
    claims_by_chunk: List[ClaimResponse]
    citations_by_chunk: List[CitationResponse]
    references: List[str]
    matches: List[ReferenceMatch]
    claim_substantiations_by_chunk: List[List[ReferenceMatch]]
