'use client';

import * as React from 'react';
import { useForm } from '@tanstack/react-form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Progress } from '../ui/progress';
import { Button } from '../ui/button';
import { useWizard } from './wizard-context';
import { Loader2 } from 'lucide-react';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Checkbox } from '../ui/checkbox';

export function ProcessStep() {
  const { state, actions } = useWizard();

  const form = useForm({
    defaultValues: state.config,
    listeners: {
      onChange: ({ formApi }) => {
        actions.setConfig(formApi.state.values);
      },
    },
    validators: {
      onChange: ({ value }) => {
        if (value.runLiteratureReview || value.runLiveReports) {
          if (!value.documentPublicationDate) {
            return {
              fields: {
                documentPublicationDate: 'Document publication date is required',
              },
            };
          }
        }
        return undefined;
      },
    },
  });

  const getStageInfo = () => {
    switch (state.processingStage) {
      case 'uploading':
        return {
          title: 'Uploading Documents',
          description: 'Uploading and converting your files...',
          detail: 'This may take a moment for large PDF files',
        };
      case 'complete':
        return {
          title: 'Upload Complete',
          description: 'Documents uploaded successfully',
          detail: 'Redirecting to analysis...',
        };
      default:
        return {
          title: 'Preparing Upload',
          description: 'Getting ready to upload your documents...',
          detail: 'Please wait',
        };
    }
  };

  if (state.analysisResults?.status === 'error') {
    return (
      <div className="space-y-6">
        <Card className="max-w-xl mx-auto border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Upload Failed</CardTitle>
            <CardDescription>There was an error processing your files</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md">
              <p className="text-sm text-destructive">{state.analysisResults.error}</p>
            </div>

            {state.uploadProgress.error && (
              <div className="mt-3">
                <p className="text-xs text-destructive whitespace-pre-line">{state.uploadProgress.error}</p>
              </div>
            )}

            <Button
              onClick={() => {
                actions.setAnalysisResults(null);
                actions.setUploadProgress({ progress: 0, status: 'idle' });
              }}
              variant="outline"
              className="w-full"
            >
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (state.isProcessing) {
    const stageInfo = getStageInfo();

    return (
      <div className="space-y-6">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 mx-auto animate-spin text-primary" />
          <h2 className="text-2xl font-bold">{stageInfo.title}</h2>
          <p className="text-muted-foreground max-w-md mx-auto">{stageInfo.description}</p>
        </div>
        <Card className="max-w-xl mx-auto">
          <CardContent className="py-8">
            <div className="space-y-4">
              <Progress value={state.uploadProgress.progress} className="w-full" />
              <p className="text-sm text-center text-muted-foreground">{stageInfo.detail}</p>

              {/* Show upload progress percentage */}
              {state.uploadProgress.status === 'uploading' && state.uploadProgress.progress > 0 && (
                <div className="text-center">
                  <p className="text-2xl font-semibold text-primary">{Math.round(state.uploadProgress.progress)}%</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Uploading {state.mainDocument?.name}
                    {state.supportingDocuments.length > 0 &&
                      ` and ${state.supportingDocuments.length} supporting file${state.supportingDocuments.length > 1 ? 's' : ''}`}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card className="max-w-xl mx-auto">
        <CardHeader>
          <CardTitle>Document Summary</CardTitle>
          <CardDescription>Documents ready for processing</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span>Main Document:</span>
              <span className="font-medium">{state.mainDocument?.name}</span>
            </div>
            <div className="flex justify-between">
              <span>Supporting Documents:</span>
              <span className="font-medium">{state.supportingDocuments.length}</span>
            </div>
            <div className="flex justify-between">
              <span>Analysis Type:</span>
              <span className="font-medium">Claims & Citations</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="max-w-xl mx-auto">
        <CardHeader>
          <CardTitle>Analysis Configuration</CardTitle>
          <CardDescription>Provide context for more accurate analysis</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form.Field name="domain">
            {(field) => (
              <div className="space-y-2">
                <Label htmlFor="domain">Domain</Label>
                <Input
                  id="domain"
                  placeholder="e.g., Healthcare, Technology, Finance..."
                  value={field.state.value}
                  onChange={(e) => field.handleChange(e.target.value)}
                />
              </div>
            )}
          </form.Field>
          <form.Field name="targetAudience">
            {(field) => (
              <div className="space-y-2">
                <Label htmlFor="target-audience">Target Audience</Label>
                <Input
                  id="target-audience"
                  placeholder="e.g., General public, Experts, Students..."
                  value={field.state.value}
                  onChange={(e) => field.handleChange(e.target.value)}
                />
              </div>
            )}
          </form.Field>
          <div className="space-y-3 pt-2">
            <form.Field name="runLiteratureReview">
              {(field) => (
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="run-literature-review"
                    checked={field.state.value}
                    onCheckedChange={(checked) => field.handleChange(checked === true)}
                  />
                  <Label
                    htmlFor="run-literature-review"
                    className="text-sm font-normal leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    Run literature review
                  </Label>
                </div>
              )}
            </form.Field>
            <form.Field name="runSuggestCitations">
              {(field) => (
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="run-suggest-citations"
                    checked={field.state.value}
                    onCheckedChange={(checked) => field.handleChange(checked === true)}
                  />
                  <Label
                    htmlFor="run-suggest-citations"
                    className="text-sm font-normal leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    Run suggest citations
                  </Label>
                </div>
              )}
            </form.Field>
            <form.Field name="runLiveReports">
              {(field) => (
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="run-live-reports"
                    checked={field.state.value}
                    onCheckedChange={(checked) => field.handleChange(checked === true)}
                  />
                  <Label
                    htmlFor="run-live-reports"
                    className="text-sm font-normal leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    Run live reports
                  </Label>
                </div>
              )}
            </form.Field>
          </div>
          {(form.state.values.runLiteratureReview || form.state.values.runLiveReports) && (
            <form.Field name="documentPublicationDate">
              {(field) => (
                <div className="space-y-2">
                  <Label htmlFor="publication-date">
                    Document Publication Date
                    <span className="text-destructive ml-1">*</span>
                  </Label>
                  <Input
                    id="publication-date"
                    type="date"
                    value={field.state.value}
                    onChange={(e) => field.handleChange(e.target.value)}
                    className={field.state.meta.errors.length > 0 ? 'border-destructive' : ''}
                  />
                  {!field.state.meta.isValid && (
                    <p className="text-sm text-destructive">{field.state.meta.errors.join(', ')}</p>
                  )}
                </div>
              )}
            </form.Field>
          )}
        </CardContent>
      </Card>

      <p className="text-muted-foreground max-w-md mx-auto text-center">
        Ready to analyze your documents for claims, citations, and accuracy
      </p>
    </div>
  );
}
