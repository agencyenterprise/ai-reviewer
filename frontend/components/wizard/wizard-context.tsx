'use client';

import * as React from 'react';
import { v4 as uuid } from 'uuid';
import { WizardContextType, WizardState, WizardActions } from './types';

const initialState: WizardState = {
  currentStep: 1,
  mainDocument: null,
  supportingDocuments: [],
  domain: '',
  targetAudience: '',
  isProcessing: false,
  analysisResults: null,
  sessionId: null,
};

const WizardContext = React.createContext<WizardContextType | undefined>(undefined);

export function WizardProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = React.useState<WizardState>(initialState);

  const actions: WizardActions = {
    setCurrentStep: (step: number) => {
      setState((prev) => ({ ...prev, currentStep: step }));
    },
    setMainDocument: (file: File | null) => {
      setState((prev) => {
        const newSessionId = file && !prev.sessionId ? uuid() : prev.sessionId;
        return { ...prev, mainDocument: file, sessionId: newSessionId };
      });
    },
    setSupportingDocuments: (files: File[]) => {
      setState((prev) => ({ ...prev, supportingDocuments: files }));
    },
    setDomain: (domain: string) => {
      setState((prev) => ({ ...prev, domain }));
    },
    setTargetAudience: (targetAudience: string) => {
      setState((prev) => ({ ...prev, targetAudience }));
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

        const updatedState = response.state;

        return {
          ...prev,
          analysisResults: {
            ...prev.analysisResults,
            fullResults: {
              ...prev.analysisResults.fullResults,
              ...updatedState,
            },
          },
        };
      });
    },
    setSessionId: (sessionId: string) => {
      setState((prev) => ({ ...prev, sessionId }));
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
