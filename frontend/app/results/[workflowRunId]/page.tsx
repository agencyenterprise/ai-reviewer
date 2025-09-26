'use client';

import { Button } from '@/components/ui/button';
import { ResultsVisualization } from '@/components/wizard/results-step/results-visualization';
import { api } from '@/lib/api';
import { ChunkReevaluationResponse, WorkflowRunDetailed } from '@/lib/generated-api';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useParams } from 'next/navigation';

export default function ResultsPage() {
  const params = useParams();
  const workflowRunId = params.workflowRunId as string;

  const queryClient = useQueryClient();

  const {
    data: workflowRun,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['workflowRun', workflowRunId],
    queryFn: () => api.getWorkflowRunApiWorkflowRunWorkflowRunIdGet({ workflowRunId }),
  });

  const handleChunkReevaluation = (response: ChunkReevaluationResponse) => {
    queryClient.setQueryData(['workflowRun', workflowRunId], (curr: WorkflowRunDetailed) => {
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

        {isLoading && (
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
              <p className="text-destructive mb-4">{error.message}</p>
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
