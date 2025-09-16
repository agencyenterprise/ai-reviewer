'use client';

import { Stepper } from '@/components/ui/stepper';
import { ProcessStep } from '@/components/wizard/process-step';
import { ResultsStep } from '@/components/wizard/results-step';
import { WizardStep } from '@/components/wizard/types';
import { UploadStep } from '@/components/wizard/upload-step';
import { useWizard, WizardProvider } from '@/components/wizard/wizard-context';
import { WizardNavigation } from '@/components/wizard/wizard-navigation';

const steps: WizardStep[] = [
  {
    id: 'upload',
    title: 'Upload Documents',
    description: 'Main & supporting files',
  },
  {
    id: 'process',
    title: 'Process',
    description: 'Start AI analysis',
  },
  {
    id: 'results',
    title: 'Results',
    description: 'View analysis results',
  },
];

function WizardContent() {
  const { state } = useWizard();

  const renderStepContent = () => {
    switch (state.currentStep) {
      case 1:
        return <UploadStep />;
      case 2:
        return <ProcessStep />;
      case 3:
        return <ResultsStep />;
      default:
        return <UploadStep />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="container mx-auto px-4 py-12 max-w-6xl">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-center mb-8 bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text text-transparent">
            Rand AI Reviewer
          </h1>

          <div className="max-w-2xl mx-auto">
            <Stepper steps={steps} currentStep={state.currentStep} className="mb-8" />
          </div>
        </div>

        <div className="bg-background/60 backdrop-blur-sm border border-border/50 rounded-2xl p-8 mb-8 shadow-sm">
          {renderStepContent()}
        </div>

        <WizardNavigation />
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <WizardProvider>
      <WizardContent />
    </WizardProvider>
  );
}
