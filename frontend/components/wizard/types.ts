export interface WizardStep {
    id: string
    title: string
    description: string
}

export interface Claim {
    text: string
    claim: string
    rationale: string
    needs_substantiation: boolean
}

export interface ClaimsByChunk {
    claims: Claim[]
    rationale: string
}

export interface Citation {
    text: string
    type: string
    format: string
    needs_bibliography: boolean
    associated_bibliography?: string
    index_of_associated_bibliography?: number
    rationale: string
}

export interface CitationsByChunk {
    citations: Citation[]
    rationale: string
}

export interface Reference {
    text: string
    has_associated_supporting_document: boolean
    index_of_associated_supporting_document: number
}

export interface ClaimSubstantiation {
    is_substantiated: boolean
    rationale: string
    feedback: string
}

export interface DetailedResults {
    claims_by_chunk: ClaimsByChunk[]
    citations_by_chunk: CitationsByChunk[]
    references: Reference[]
    claim_substantiations_by_chunk: ClaimSubstantiation[][]
}

export interface AnalysisResults {
    claimsDetected: number
    citationsFound: number
    unsubstantiatedClaims: number
    status: "processing" | "completed" | "error"
    error?: string
    fullResults?: DetailedResults
}

export interface WizardState {
    currentStep: number
    mainDocument: File | null
    supportingDocuments: File[]
    isProcessing: boolean
    analysisResults: AnalysisResults | null
}

export interface WizardActions {
    setCurrentStep: (step: number) => void
    setMainDocument: (file: File | null) => void
    setSupportingDocuments: (files: File[]) => void
    setIsProcessing: (processing: boolean) => void
    setAnalysisResults: (results: AnalysisResults | null) => void
    reset: () => void
}

export interface WizardContextType {
    state: WizardState
    actions: WizardActions
}
