from lib.workflows.abbreviation_scan_v2.state import (
    AbbreviationScanV2Config,
    AbbreviationScanV2State,
)
from lib.workflows.about_this_ger.state import (
    AboutThisGerConfig,
    AboutThisGerState,
)
from lib.workflows.simple_deep_agent.state import (
    SimpleDeepAgentConfig,
    SimpleDeepAgentState,
)
from lib.workflows.chunk_splitting.state import (
    ChunkSplittingState,
    ChunkSplittingWorkflowConfig,
)
from lib.workflows.citation_detection.state import (
    CitationDetectionConfig,
    CitationDetectionState,
)
from lib.workflows.claim_extraction.state import (
    ClaimExtractionState,
    ClaimExtractionWorkflowConfig,
)
from lib.workflows.claim_reference_validation_v2.state import (
    ClaimReferenceValidationV2Config,
    ClaimReferenceValidationV2State,
)
from lib.workflows.document_processing.state import (
    DocumentProcessingState,
    DocumentProcessingWorkflowConfig,
)
from lib.workflows.document_summarization.state import (
    DocumentSummarizationState,
    DocumentSummarizationWorkflowConfig,
)
from lib.workflows.footnote_extraction.state import (
    FootnoteExtractionConfig,
    FootnoteExtractionState,
)
from lib.workflows.human_approval.state import (
    HumanApprovalConfig,
    HumanApprovalState,
)
from lib.workflows.methodological_alignment.state import (
    MethodologicalAlignmentState,
    MethodologicalAlignmentWorkflowConfig,
)
from lib.workflows.reference_downloader.state import (
    ReferenceDownloaderState,
    ReferenceDownloaderWorkflowConfig,
)
from lib.workflows.reference_extraction.state import (
    ReferenceExtractionConfig,
    ReferenceExtractionState,
)
from lib.workflows.reference_file_matching.state import (
    ReferenceFileMatchingConfig,
    ReferenceFileMatchingState,
)
from lib.workflows.reference_validation.state import (
    ReferenceValidationState,
    ReferenceValidationWorkflowConfig,
)
from lib.workflows.reference_validation_v2.state import (
    ReferenceValidationV2State,
    ReferenceValidationV2WorkflowConfig,
)
from lib.workflows.results_extraction.state import (
    ResultsExtractionState,
    ResultsExtractionWorkflowConfig,
)
from lib.workflows.reviewer_2.state import (
    Reviewer2Config,
    Reviewer2State,
)

WorkflowState = (
    AboutThisGerState
    | DocumentProcessingState
    | ChunkSplittingState
    | DocumentSummarizationState
    | ReferenceExtractionState
    | ReferenceFileMatchingState
    | FootnoteExtractionState
    | ClaimExtractionState
    | ClaimReferenceValidationV2State
    | CitationDetectionState
    | AbbreviationScanV2State
    | MethodologicalAlignmentState
    | ReferenceDownloaderState
    | ReferenceValidationState
    | ReferenceValidationV2State
    | ResultsExtractionState
    | HumanApprovalState
    | Reviewer2State
    | SimpleDeepAgentState
)

WorkflowConfig = (
    AboutThisGerConfig
    | DocumentProcessingWorkflowConfig
    | ChunkSplittingWorkflowConfig
    | DocumentSummarizationWorkflowConfig
    | ReferenceExtractionConfig
    | ReferenceFileMatchingConfig
    | FootnoteExtractionConfig
    | ClaimExtractionWorkflowConfig
    | CitationDetectionConfig
    | ClaimReferenceValidationV2Config
    | AbbreviationScanV2Config
    | MethodologicalAlignmentWorkflowConfig
    | ReferenceDownloaderWorkflowConfig
    | ReferenceValidationWorkflowConfig
    | ReferenceValidationV2WorkflowConfig
    | ResultsExtractionWorkflowConfig
    | HumanApprovalConfig
    | Reviewer2Config
    | SimpleDeepAgentConfig
)
