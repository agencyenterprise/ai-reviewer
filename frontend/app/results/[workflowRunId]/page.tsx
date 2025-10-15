'use client';

import { Button } from '@/components/ui/button';
import { ResultsVisualization } from '@/components/wizard/results-step/results-visualization';
import { workflowsApi } from '@/lib/api';
import { ChunkReevaluationResponse, WorkflowRunDetailed, WorkflowRunStatus } from '@/lib/generated-api';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect } from 'react';
import { toast } from 'sonner';

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
    refetchInterval: ({ state }) => (state.data?.run.status === WorkflowRunStatus.Running ? 3000 : false),
    queryFn: () => workflowsApi.getWorkflowRunApiWorkflowRunWorkflowRunIdGet({ workflowRunId }),
  });

  const isProcessing = workflowRun?.run.status === WorkflowRunStatus.Running;

  const handleChunkReevaluation = (response: ChunkReevaluationResponse) => {
    queryClient.setQueryData(['workflowRun', workflowRunId], (curr: WorkflowRunDetailed) => {
      return {
        ...curr,
        state: { ...curr.state, ...response.state },
      };
    });
  };

  useEffect(() => {
    let toastId: string | number | undefined;
    if (isProcessing) {
      toastId = toast.loading('Analysis in progress', {
        description: 'Results will update automatically as sections complete',
      });
    }

    return () => {
      if (toastId) {
        toast.dismiss(toastId);
      }
    };
  }, [isProcessing]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
        <div className="container mx-auto px-4 py-12 max-w-6xl">
          <div className="flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading workflow run...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
        <div className="container mx-auto px-4 py-12 max-w-6xl">
          <div className="flex items-center justify-center">
            <div className="text-center">
              <p className="text-destructive mb-4">{error.message}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!workflowRun) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="container mx-auto px-4 py-12 max-w-6xl">
        <div className="flex items-center justify-between mb-6">
          <hgroup>
            <h1 className="text-2xl font-bold">{workflowRun.run.title}</h1>
            <h2 className="text-muted-foreground text-sm">
              Workflow Run Results · {format(workflowRun.run.createdAt || new Date(), 'MMM d, yyyy')}
            </h2>
          </hgroup>
          <Link href="/">
            <Button variant="outline">Back to Home</Button>
          </Link>
        </div>

        <ResultsVisualization
          results={workflowRun.state || undefined}
          onChunkReevaluation={handleChunkReevaluation}
          isProcessing={isProcessing}
        />
      </div>
    </div>
  );
}
