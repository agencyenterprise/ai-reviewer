'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { WorkflowRun } from '@/lib/generated-api';
import { api } from '@/lib/api';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';

interface WorkflowRunsListProps {
  className?: string;
}

export function WorkflowRunsList({ className }: WorkflowRunsListProps) {
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRuns = async () => {
      try {
        setLoading(true);
        const workflowRuns = await api.listWorkflowRunsApiWorkflowRunsGet();
        setRuns(workflowRuns);
      } catch (err) {
        console.error('Failed to fetch workflow runs:', err);
        setError('Failed to load previous runs');
      } finally {
        setLoading(false);
      }
    };

    fetchRuns();
  }, []);

  if (loading) {
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
            <p className="text-destructive">{error}</p>
            <Button variant="outline" onClick={() => window.location.reload()} className="mt-2">
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (runs.length === 0) {
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
          {runs.map((run) => (
            <div
              key={run.id}
              className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div>
                <h3 className="font-medium truncate">{run.title}</h3>

                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <p>{formatDistanceToNow(run.createdAt, { addSuffix: true })}</p>
                </div>
              </div>

              <Link href={`/results/${run.id}`}>
                <Button variant="outline" size="sm" className="ml-4">
                  View Results
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
