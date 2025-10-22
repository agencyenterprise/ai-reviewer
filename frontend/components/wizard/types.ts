import { ClaimSubstantiatorStateOutput, ChunkReevaluationResponse } from '@/lib/generated-api';

export interface WizardStep {
  id: string;
  title: string;
  description: string;
}

export interface AnalysisConfig {
  domain: string;
  targetAudience: string;
  documentPublicationDate: string;
  runLiteratureReview: boolean;
  runSuggestCitations: boolean;
  runLiveReports: boolean;
}

export interface AnalysisResults {
  status: 'processing' | 'completed' | 'error';
  error?: string;
  fullResults?: ClaimSubstantiatorStateOutput;
}

export type ProcessingStage = 'idle' | 'uploading' | 'complete';

export interface UploadProgress {
  progress: number; // 0-100
  status: 'idle' | 'uploading' | 'complete' | 'error';
  error?: string;
}

export interface WizardState {
  currentStep: number;
  mainDocument: File | null;
  supportingDocuments: File[];
  config: AnalysisConfig;
  isProcessing: boolean;
  processingStage: ProcessingStage;
  uploadProgress: UploadProgress;
  workflowRunId: string | null;
  analysisResults: AnalysisResults | null;
  sessionId: string | null;
}

export interface WizardActions {
  setCurrentStep: (step: number) => void;
  setMainDocument: (file: File | null) => void;
  setSupportingDocuments: (files: File[]) => void;
  setConfig: (config: AnalysisConfig) => void;
  setIsProcessing: (processing: boolean) => void;
  setProcessingStage: (stage: ProcessingStage) => void;
  setUploadProgress: (progress: UploadProgress) => void;
  setWorkflowRunId: (id: string | null) => void;
  setAnalysisResults: (results: AnalysisResults | null) => void;
  updateChunkResults: (response: ChunkReevaluationResponse) => void;
  setSessionId: (sessionId: string) => void;
  reset: () => void;
}

export interface WizardContextType {
  state: WizardState;
  actions: WizardActions;
}
