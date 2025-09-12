'use client';

import * as React from 'react';
import { CheckCircle, XCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Progress } from '../../ui/progress';
import { useWizard } from '../wizard-context';
import { ResultsVisualization } from './results-visualization';

export function ResultsStep() {
  const { state } = useWizard();
  const hasError = state.analysisResults?.status === 'error';

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        {hasError ? (
          <XCircle className="w-12 h-12 mx-auto text-red-500" />
        ) : (
          <CheckCircle className="w-12 h-12 mx-auto text-green-500" />
        )}
        <h2 className="text-2xl font-bold">
          {state.isProcessing ? 'Processing...' : hasError ? 'Analysis Failed' : 'Analysis Complete'}
        </h2>
        <p className="text-muted-foreground max-w-md mx-auto">
          {state.isProcessing
            ? 'AI is analyzing your documents for claims, citations, and accuracy...'
            : hasError
              ? 'There was an error processing your documents. Please try again.'
              : 'Your document analysis has been completed successfully!'}
        </p>
      </div>

      {state.isProcessing ? (
        <Card className="max-w-xl mx-auto">
          <CardContent className="py-8">
            <div className="space-y-4">
              <Progress value={65} className="w-full" />
              <p className="text-sm text-center text-muted-foreground">Detecting claims and verifying citations...</p>
            </div>
          </CardContent>
        </Card>
      ) : hasError ? (
        <Card className="max-w-xl mx-auto border-red-200">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
            <CardDescription>Failed to analyze {state.mainDocument?.name}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700">
                {state.analysisResults?.error || 'An unknown error occurred during processing.'}
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <ResultsVisualization results={state.analysisResults} />
      )}
    </div>
  );
}
