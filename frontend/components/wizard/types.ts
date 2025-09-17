import { ClaimSubstantiatorState } from '@/lib/generated-api';

export interface WizardStep {
  id: string;
  title: string;
  description: string;
}

export interface AnalysisResults {
  status: 'processing' | 'completed' | 'error';
  error?: string;
  fullResults?: ClaimSubstantiatorState;
}

export interface WizardState {
  currentStep: number;
  mainDocument: File | null;
  supportingDocuments: File[];
  isProcessing: boolean;
  analysisResults: AnalysisResults | null;
}

export interface WizardActions {
  setCurrentStep: (step: number) => void;
  setMainDocument: (file: File | null) => void;
  setSupportingDocuments: (files: File[]) => void;
  setIsProcessing: (processing: boolean) => void;
  setAnalysisResults: (results: AnalysisResults | null) => void;
  updateChunkResults: (chunkIndex: number, updatedResults: Record<string, unknown>) => void;
  reset: () => void;
}

export interface WizardContextType {
  state: WizardState;
  actions: WizardActions;
}
