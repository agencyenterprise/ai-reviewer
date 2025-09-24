import { ClaimSubstantiatorStateOutput, ChunkReevaluationResponse } from '@/lib/generated-api';

export interface WizardStep {
  id: string;
  title: string;
  description: string;
}

export interface AnalysisResults {
  status: 'processing' | 'completed' | 'error';
  error?: string;
  fullResults?: ClaimSubstantiatorStateOutput;
}

export interface WizardState {
  currentStep: number;
  mainDocument: File | null;
  supportingDocuments: File[];
  domain: string;
  targetAudience: string;
  isProcessing: boolean;
  analysisResults: AnalysisResults | null;
}

export interface WizardActions {
  setCurrentStep: (step: number) => void;
  setMainDocument: (file: File | null) => void;
  setSupportingDocuments: (files: File[]) => void;
  setDomain: (domain: string) => void;
  setTargetAudience: (targetAudience: string) => void;
  setIsProcessing: (processing: boolean) => void;
  setAnalysisResults: (results: AnalysisResults | null) => void;
  updateChunkResults: (response: ChunkReevaluationResponse) => void;
  reset: () => void;
}

export interface WizardContextType {
  state: WizardState;
  actions: WizardActions;
}
