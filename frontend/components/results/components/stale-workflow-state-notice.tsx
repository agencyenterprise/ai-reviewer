'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, Check, Copy, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Callout } from '@/components/ui/callout';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { getWorkflowRawStateApiWorkflowsWorkflowRunIdRawStateGet } from '@/lib/generated-api';

interface StaleWorkflowStateNoticeProps {
  workflowRunId: string;
  workflowName: string;
}

/**
 * Shown when a run completed but its saved state no longer matches the
 * assessment's current state model — i.e. the assessment changed shape since
 * the run.
 *
 * The run's data is still on the row, it just cannot be rendered by the current
 * result views, so the raw JSON is offered as an escape hatch. It is fetched
 * lazily rather than shipped with the project payload: these blobs run to
 * several MB and are only ever wanted for the one run being looked at.
 */
export function StaleWorkflowStateNotice({ workflowRunId, workflowName }: StaleWorkflowStateNoticeProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  // Stringified in `select` rather than during render: these payloads reach
  // several MB, and re-running JSON.stringify on every re-render (toggling the
  // "Copied" label alone would do it) is enough to visibly freeze the UI.
  const {
    data: rawJson,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['workflow-raw-state', workflowRunId],
    enabled: isOpen,
    staleTime: Infinity,
    queryFn: async () =>
      await getWorkflowRawStateApiWorkflowsWorkflowRunIdRawStateGet({
        path: { workflow_run_id: workflowRunId },
      }),
    select: (response) => (response.state_json ? JSON.stringify(response.state_json, null, 2) : null),
  });

  const handleCopy = async () => {
    if (!rawJson) return;
    await navigator.clipboard.writeText(rawJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Callout title="Results unavailable — assessment updated" variant="warning" icon={AlertTriangle}>
      <p className="text-sm">
        <strong>{workflowName}</strong> has been updated since this run, so its saved results can no longer be
        displayed. Re-run the assessment to see current results.
      </p>

      <Collapsible open={isOpen} onOpenChange={setIsOpen} className="mt-3">
        <CollapsibleTrigger asChild>
          <Button variant="outline" size="sm">
            {isOpen ? 'Hide raw data' : 'View raw data'}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="mt-2">
          {isLoading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading raw data…
            </div>
          )}
          {error && <p className="text-sm text-destructive">Could not load the raw data for this run.</p>}
          {!isLoading && !error && !rawJson && (
            <p className="text-sm text-muted-foreground">This run has no saved data.</p>
          )}
          {rawJson && (
            <div className="space-y-2">
              <Button variant="ghost" size="sm" onClick={handleCopy}>
                {copied ? <Check className="mr-1 h-4 w-4" /> : <Copy className="mr-1 h-4 w-4" />}
                {copied ? 'Copied' : 'Copy JSON'}
              </Button>
              <pre className="max-h-96 overflow-auto rounded-md border bg-muted p-3 text-xs">{rawJson}</pre>
            </div>
          )}
        </CollapsibleContent>
      </Collapsible>
    </Callout>
  );
}
