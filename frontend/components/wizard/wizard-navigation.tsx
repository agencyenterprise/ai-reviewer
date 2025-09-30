'use client';

import { analysisService } from '@/lib/analysis-service';
import { cn } from '@/lib/utils';
import { Play } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Button } from '../ui/button';
import { useWizard } from './wizard-context';

export function WizardNavigation() {
  const router = useRouter();
  const { state, actions } = useWizard();

  const canProceedFromStep1 = state.mainDocument !== null;

  const handleNext = async () => {
    if (state.currentStep < 3) {
      if (state.currentStep === 2) {
        actions.setIsProcessing(true);

        try {
          const analysisResults = await analysisService.runClaimSubstantiation({
            mainDocument: state.mainDocument!,
            supportingDocuments: state.supportingDocuments,
            config: {
              useToulmin: true,
              domain: state.domain || undefined,
              targetAudience: state.targetAudience || undefined,
              sessionId: state.sessionId,
            },
          });

          actions.setAnalysisResults(analysisResults);
        } catch (error) {
          console.error('Unexpected error during analysis:', error);
          actions.setAnalysisResults({
            status: 'error',
            error: 'An unexpected error occurred during analysis',
          });
        }

        actions.setIsProcessing(false);
      }
      actions.setCurrentStep(state.currentStep + 1);
    } else if (state.currentStep === 3) {
      actions.reset();
    }
  };

  const handleBack = () => {
    if (state.currentStep > 1) {
      actions.setCurrentStep(state.currentStep - 1);
    } else {
      router.push('/');
    }
  };

  const getNextButtonText = () => {
    switch (state.currentStep) {
      case 1:
        return 'Next';
      case 2:
        return (
          <p className="flex items-center gap-2">
            <Play className="w-4 h-4" /> Start Analysis
          </p>
        );
      case 3:
        return 'Start New Analysis';
      default:
        return 'Next';
    }
  };

  const isNextDisabled = () => {
    return state.isProcessing || (state.currentStep === 1 && !canProceedFromStep1);
  };

  return (
    <div className="flex items-center justify-between max-w-4xl mx-auto pt-8">
      <Button
        variant="outline"
        onClick={handleBack}
        disabled={state.isProcessing}
        className={cn(
          'px-6 py-2.5 font-medium transition-all duration-200',
          'hover:bg-muted hover:border-muted-foreground/20',
          'disabled:opacity-50 disabled:cursor-not-allowed',
        )}
      >
        Back
      </Button>

      <div className="flex items-center gap-4">
        {state.currentStep === 1 && !state.mainDocument && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/50 px-3 py-1.5 rounded-full">
            <div className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
            Upload main document to continue
          </div>
        )}

        <Button
          onClick={handleNext}
          disabled={isNextDisabled()}
          className={cn(
            'px-8 py-2.5 font-semibold transition-all duration-200',
            'hover:shadow-md hover:scale-105 active:scale-95',
            'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:shadow-none',
            state.currentStep === 2 &&
              'bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70',
            state.currentStep === 3 &&
              'bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600',
          )}
        >
          {getNextButtonText()}
        </Button>
      </div>
    </div>
  );
}
