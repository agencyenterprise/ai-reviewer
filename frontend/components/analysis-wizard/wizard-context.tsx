'use client';

import { createContext, useContext, useState, useCallback, useMemo, ReactNode } from 'react';
import { WorkflowRunType } from '@/lib/generated-api';
import { DEFAULT_SELECTED_WORKFLOW_TYPES, hasSupportingDocumentsRequirement } from '@/components/workflows/utils';
import { useVisibleWorkflowTypes } from '@/lib/hooks/use-visible-workflow-types';

export type PreflightStatus = 'idle' | 'pending' | 'valid' | 'invalid';
export type WizardStep = 1 | 2;

interface WizardState {
  currentStep: WizardStep;
  mainDocument: File | null;
  projectId: string | null;
  preflightStatus: { format: PreflightStatus };
  selectedWorkflowTypes: WorkflowRunType[];
  needsReferencesStep: boolean;
}

interface WizardContextValue extends WizardState {
  setMainDocument: (file: File | null) => void;
  setProjectId: (id: string) => void;
  setPreflightStatus: (status: Partial<WizardState['preflightStatus']>) => void;
  setSelectedWorkflowTypes: (types: WorkflowRunType[]) => void;
  nextStep: () => void;
}

const WizardContext = createContext<WizardContextValue | null>(null);

interface WizardProviderProps {
  children: ReactNode;
}

export function WizardProvider({ children }: WizardProviderProps) {
  const [currentStep, setCurrentStep] = useState<WizardStep>(1);
  const [mainDocument, setMainDocument] = useState<File | null>(null);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [preflightStatus, setPreflightStatusState] = useState<WizardState['preflightStatus']>({
    format: 'idle',
  });
  // `null` means the user has not touched the assessment checkboxes yet, so the
  // recommended default set applies. An explicit array — including an empty one,
  // after unchecking everything — always wins.
  const [chosenWorkflowTypes, setSelectedWorkflowTypes] = useState<WorkflowRunType[] | null>(null);
  const { visibleTypes } = useVisibleWorkflowTypes();

  // Intersected with what is actually on offer: an assessment that is hidden for
  // this user (experimental, opt-in only) must never be started from a checkbox
  // they cannot see or uncheck.
  const selectedWorkflowTypes = useMemo(
    () => chosenWorkflowTypes ?? DEFAULT_SELECTED_WORKFLOW_TYPES.filter((type) => visibleTypes.includes(type)),
    [chosenWorkflowTypes, visibleTypes],
  );

  const needsReferencesStep = useMemo(
    () => hasSupportingDocumentsRequirement(selectedWorkflowTypes),
    [selectedWorkflowTypes],
  );

  const setPreflightStatus = useCallback((status: Partial<WizardState['preflightStatus']>) => {
    setPreflightStatusState((prev) => ({ ...prev, ...status }));
  }, []);

  const nextStep = useCallback(() => {
    setCurrentStep((prev) => (prev < 2 ? ((prev + 1) as WizardStep) : prev));
  }, []);

  const value = useMemo(
    () => ({
      currentStep,
      mainDocument,
      projectId,
      preflightStatus,
      selectedWorkflowTypes,
      needsReferencesStep,
      setMainDocument,
      setProjectId,
      setPreflightStatus,
      setSelectedWorkflowTypes,
      nextStep,
    }),
    [
      currentStep,
      mainDocument,
      projectId,
      preflightStatus,
      selectedWorkflowTypes,
      needsReferencesStep,
      setPreflightStatus,
      nextStep,
    ],
  );

  return <WizardContext.Provider value={value}>{children}</WizardContext.Provider>;
}

export function useWizard() {
  const context = useContext(WizardContext);
  if (!context) throw new Error('useWizard must be used within WizardProvider');
  return context;
}
