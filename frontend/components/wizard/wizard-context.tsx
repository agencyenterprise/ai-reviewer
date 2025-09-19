'use client';

import * as React from 'react';
import { WizardContextType, WizardState, WizardActions } from './types';

const initialState: WizardState = {
  currentStep: 1,
  mainDocument: null,
  supportingDocuments: [],
  isProcessing: false,
  analysisResults: null,
};

const WizardContext = React.createContext<WizardContextType | undefined>(undefined);

export function WizardProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = React.useState<WizardState>(initialState);

  const actions: WizardActions = {
    setCurrentStep: (step: number) => {
      setState((prev) => ({ ...prev, currentStep: step }));
    },
    setMainDocument: (file: File | null) => {
      setState((prev) => ({ ...prev, mainDocument: file }));
    },
    setSupportingDocuments: (files: File[]) => {
      setState((prev) => ({ ...prev, supportingDocuments: files }));
    },
    setIsProcessing: (processing: boolean) => {
      setState((prev) => ({ ...prev, isProcessing: processing }));
    },
    setAnalysisResults: (results) => {
      setState((prev) => ({ ...prev, analysisResults: results }));
    },
    updateChunkResults: (response) => {
      setState((prev) => {
        if (!prev.analysisResults?.fullResults) return prev;

        const newResults = { ...prev.analysisResults.fullResults };
        const { chunkIndex, claimsByChunk, citationsByChunk, claimSubstantiationsByChunk } = response;

        if (claimsByChunk) newResults.claimsByChunk![chunkIndex] = claimsByChunk;
        if (citationsByChunk) newResults.citationsByChunk![chunkIndex] = citationsByChunk;
        if (claimSubstantiationsByChunk)
          newResults.claimSubstantiationsByChunk![chunkIndex] = claimSubstantiationsByChunk;

        return {
          ...prev,
          analysisResults: { ...prev.analysisResults, fullResults: newResults },
        };
      });
    },
    reset: () => {
      setState(initialState);
    },
  };

  return <WizardContext.Provider value={{ state, actions }}>{children}</WizardContext.Provider>;
}

export function useWizard() {
  const context = React.useContext(WizardContext);
  if (context === undefined) {
    throw new Error('useWizard must be used within a WizardProvider');
  }
  return context;
}
