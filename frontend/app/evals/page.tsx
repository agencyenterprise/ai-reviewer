'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FileUpload } from '@/components/ui/file-upload';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { AgentSummaryCard, groupTestCasesByAgent } from './agent-summary-card';
import { TestResults } from './types';

export default function EvalsPage() {
  const [uploadedData, setUploadedData] = useState<TestResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showOnlyFailed, setShowOnlyFailed] = useState(false);

  const handleFilesChange = (files: File[]) => {
    setError(null);

    if (files.length === 0) {
      setUploadedData(null);
      return;
    }

    const file = files[0]; // Only process the first file

    if (file.type !== 'application/json') {
      setError('Please upload a JSON file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const parsedData = JSON.parse(content) as TestResults;
        setUploadedData(parsedData);
      } catch {
        setError('Invalid JSON format. Please check your file.');
      }
    };
    reader.readAsText(file);
  };

  const calculateSummaryMetrics = (data: TestResults | null) => {
    if (!data) {
      return { total: 0, passed: 0, failed: 0, accuracy: 0, duration: 0 };
    }

    const total = data.summary.total;
    const passed = data.summary.passed;
    const failed = data.summary.failed;
    const accuracy = total > 0 ? Math.round((passed / total) * 100) : 0;
    const duration = data.duration;

    return { total, passed, failed, accuracy, duration };
  };

  const metrics = calculateSummaryMetrics(uploadedData);
  const agentSummaries = uploadedData ? groupTestCasesByAgent(uploadedData.tests) : [];

  return (
    <div className="container mx-auto p-6 max-w-5xl">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Evaluation Results</h1>
            <p className="text-muted-foreground">Upload a JSON file containing evaluation results to view the data</p>
          </div>
          <Link href="/">
            <Button variant="ghost" size="sm" className="mb-2">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Button>
          </Link>
        </div>

        {!uploadedData && (
          <Card>
            <CardHeader>
              <CardTitle>Upload Evaluation Results</CardTitle>
              <CardDescription>
                Upload a JSON file containing evaluation results in the expected format.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FileUpload
                accept=".json,application/json"
                acceptLabel="JSON"
                multiple={false}
                maxSize={10}
                onFilesChange={handleFilesChange}
              />
            </CardContent>
          </Card>
        )}

        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-red-700">
                <div className="w-2 h-2 bg-red-500 rounded-full" />
                <p className="text-sm font-medium">{error}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {uploadedData && (
          <div className="space-y-6">
            {/* Summary Stats */}
            <Card>
              <CardHeader>
                <CardTitle>Evaluation Summary</CardTitle>
                <CardDescription>Overview of test results across all evaluation cases</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-5 gap-4">
                  <div className="text-center p-4 bg-muted/30 rounded-lg">
                    <div className="text-2xl font-bold text-foreground">{metrics.total}</div>
                    <div className="text-sm text-muted-foreground">Total Tests</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">{metrics.passed}</div>
                    <div className="text-sm text-muted-foreground">Passed</div>
                  </div>
                  <div className="text-center p-4 bg-red-50 rounded-lg">
                    <div className="text-2xl font-bold text-red-600">{metrics.failed}</div>
                    <div className="text-sm text-muted-foreground">Failed</div>
                  </div>
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">{metrics.accuracy}%</div>
                    <div className="text-sm text-muted-foreground">Accuracy</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">{metrics.duration.toFixed(1)}s</div>
                    <div className="text-sm text-muted-foreground">Duration</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Agent Summaries */}
            {agentSummaries.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold">Results by Agent</h2>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="show-only-failed"
                      checked={showOnlyFailed}
                      onCheckedChange={(checked) => setShowOnlyFailed(checked === true)}
                    />
                    <label
                      htmlFor="show-only-failed"
                      className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                      Show only failed tests
                    </label>
                  </div>
                </div>
                <div className="space-y-4">
                  {agentSummaries.map((summary, index) => (
                    <AgentSummaryCard key={index} summary={summary} showOnlyFailed={showOnlyFailed} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
