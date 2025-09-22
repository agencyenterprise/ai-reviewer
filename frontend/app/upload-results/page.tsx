'use client';

import { Button } from '@/components/ui/button';
import { FileUpload } from '@/components/ui/file-upload';
import { ResultsStep } from '@/components/wizard/results-step';
import { AnalysisResults } from '@/components/wizard/types';
import { WizardProvider } from '@/components/wizard/wizard-context';
import Link from 'next/link';
import * as React from 'react';

export default function UploadResultsPage() {
  const [uploadedFile, setUploadedFile] = React.useState<File | null>(null);
  const [isProcessing, setIsProcessing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [analysisResults, setAnalysisResults] = React.useState<AnalysisResults | null>(null);
  const [showResults, setShowResults] = React.useState(false);

  const handleFileUpload = React.useCallback((files: File[]) => {
    const file = files[0]; // Take the first file since we only want one JSON file
    if (file) {
      setUploadedFile(file);
      setError(null);
      setAnalysisResults(null);
      setShowResults(false);
    }
  }, []);

  const processFile = React.useCallback(async () => {
    if (!uploadedFile) return;

    setIsProcessing(true);
    setError(null);

    try {
      const text = await uploadedFile.text();
      const jsonData = JSON.parse(text);
      setAnalysisResults(jsonData);
      setShowResults(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to process file';
      setError(`Error processing file: ${errorMessage}`);
    } finally {
      setIsProcessing(false);
    }
  }, [uploadedFile]);

  const resetUpload = React.useCallback(() => {
    setUploadedFile(null);
    setError(null);
    setAnalysisResults(null);
    setShowResults(false);
    setIsProcessing(false);
  }, []);

  const renderContent = () => {
    if (showResults && analysisResults) {
      return (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-semibold">Analysis Results</h2>
            <div className="flex gap-2">
              <Link href="/">
                <Button variant="outline">Start New Analysis</Button>
              </Link>
              <Button variant="outline" onClick={resetUpload}>
                Upload Another File
              </Button>
            </div>
          </div>

          <WizardProvider>
            <ResultsStep uploadedResults={analysisResults} />
          </WizardProvider>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <label className="text-sm font-medium">JSON Results File</label>
          <FileUpload
            accept=".json"
            acceptLabel="JSON"
            multiple={false}
            maxSize={50} // Allow larger JSON files (50MB)
            onFilesChange={handleFileUpload}
            className="w-full"
          />
        </div>

        {uploadedFile && (
          <div className="p-3 bg-muted rounded-md">
            <p className="text-sm text-muted-foreground">
              Selected file: <span className="font-medium">{uploadedFile.name}</span>
            </p>
            <p className="text-xs text-muted-foreground">Size: {(uploadedFile.size / 1024).toFixed(1)} KB</p>
          </div>
        )}

        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        <div className="flex gap-2">
          <Button onClick={processFile} disabled={!uploadedFile || isProcessing} className="flex-1">
            {isProcessing ? 'Processing...' : 'View Results'}
          </Button>

          {uploadedFile && (
            <Button variant="outline" onClick={resetUpload}>
              Clear
            </Button>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="container mx-auto px-4 py-12 max-w-6xl">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-center mb-8 bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text text-transparent">
            Upload saved analysis results
          </h1>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto mb-6">
            Upload a JSON file containing the results of a previous analysis run to view them in the results viewer.
          </p>
        </div>

        <div className="bg-background/60 backdrop-blur-sm border border-border/50 rounded-2xl p-8 shadow-sm">
          {renderContent()}
        </div>
      </div>
    </div>
  );
}
