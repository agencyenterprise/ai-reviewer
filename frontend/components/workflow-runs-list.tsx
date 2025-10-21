'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusIndicator } from '@/components/ui/status-indicator';
import { DeleteWorkflowRunDialog } from './workflow-runs-list/delete-workflow-run-dialog';
import { workflowsApi } from '@/lib/api';
import { useQuery } from '@tanstack/react-query';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';

interface WorkflowRunsListProps {
  className?: string;
}

export function WorkflowRunsList({ className }: WorkflowRunsListProps) {
  const {
    data: runs,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['workflowRuns'],
    refetchInterval: 3000,
    queryFn: () => workflowsApi.listWorkflowRunsApiWorkflowRunsGet(),
  });

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Previous Runs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="mt-2 text-muted-foreground">Loading previous runs...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Previous Runs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-destructive">{error.message}</p>
            <Button variant="outline" onClick={() => window.location.reload()} className="mt-2">
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (runs?.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Previous Runs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-muted-foreground">No previous runs found</p>
            <p className="text-sm text-muted-foreground mt-1">Upload and process documents to see them here</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Previous Analyses</CardTitle>
        <p className="text-sm text-muted-foreground">View and revisit your previous document analyses</p>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {runs?.map((run) => (
            <div
              key={run.id}
              className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-medium truncate">{run.title}</h3>
                  <StatusIndicator status={run.status} />
                </div>

                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <p>{formatDistanceToNow(run.createdAt, { addSuffix: true })}</p>
                </div>
              </div>

              <div className="flex gap-2">
                <Link href={`/results/${run.id}`}>
                  <Button variant="outline" size="sm">
                    View Results
                  </Button>
                </Link>

                <DeleteWorkflowRunDialog workflowRunId={run.id} workflowRunTitle={run.title} />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
