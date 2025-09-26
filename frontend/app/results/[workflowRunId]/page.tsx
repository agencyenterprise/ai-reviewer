'use client';

import { Button } from '@/components/ui/button';
import { ResultsVisualization } from '@/components/wizard/results-step/results-visualization';
import { api } from '@/lib/api';
import { ChunkReevaluationResponse, WorkflowRunDetailed } from '@/lib/generated-api';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function ResultsPage() {
  const params = useParams();
  const workflowRunId = params.workflowRunId as string;

  const [workflowRun, setWorkflowRun] = useState<WorkflowRunDetailed | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchWorkflowRun() {
      if (!workflowRunId) return;

      try {
        setLoading(true);
        setError(null);
        const run = await api.getWorkflowRunApiWorkflowRunWorkflowRunIdGet({ workflowRunId });
        setWorkflowRun(run);
      } catch (err) {
        console.error('Failed to load workflow run:', err);
        setError('Failed to load workflow run');
      } finally {
        setLoading(false);
      }
    }

    fetchWorkflowRun();
  }, [workflowRunId]);

  const handleChunkReevaluation = (response: ChunkReevaluationResponse) => {
    setWorkflowRun((curr) => {
      if (!curr) return curr;

      return {
        ...curr,
        state: { ...curr.state, ...response.state },
      };
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="container mx-auto px-4 py-12 max-w-6xl">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text text-transparent">
            Workflow Run Results
          </h1>
          <Link href="/">
            <Button variant="outline">Back to Home</Button>
          </Link>
        </div>

        {loading && (
          <div className="flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading workflow run...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center">
            <div className="text-center">
              <p className="text-destructive mb-4">{error}</p>
            </div>
          </div>
        )}

        {workflowRun && (
          <ResultsVisualization
            results={workflowRun.state || undefined}
            onChunkReevaluation={handleChunkReevaluation}
          />
        )}
      </div>
    </div>
  );
}
