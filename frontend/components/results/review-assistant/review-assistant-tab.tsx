'use client';

import { HelpLink } from '@/components/help/help-link';
import { TabError, TabLoading } from '@/components/results/tab-status';
import { StatusIndicator } from '@/components/ui/status-indicator';
import { ProjectOverview, ReviewAssistantRequestSummary, WorkflowRunStatus } from '@/lib/generated-api';
import { RAIL_ITEM_ACTIVE, RAIL_ITEM_IDLE } from '@/lib/rail-style';
import { cn } from '@/lib/utils';
import { getDisplayStatus, isWorkflowProcessing } from '@/lib/workflow-state';
import { format } from 'date-fns';
import { Plus } from 'lucide-react';
import { useState } from 'react';
import { Rail, RailToggle, useRailState } from '../panes';
import { outputTitle } from './outputs';
import { RequestComposer } from './request-composer';
import { RequestView } from './request-view';
import { useReviewAssistantRequests } from './use-review-assistant';

interface ReviewAssistantTabProps {
  overview: ProjectOverview;
  readOnly: boolean;
}

/** What the main pane shows: the composer, or one request by its run id. */
type Selection = { kind: 'new' } | { kind: 'request'; runId: string };

/**
 * Review Assistant, output first: pick what you need, hand over every document
 * you have, and get it. Past requests sit in the rail, newest first, in any
 * order the author happened to need them.
 */
export function ReviewAssistantTab({ overview, readOnly }: ReviewAssistantTabProps) {
  const projectId = overview.project.id;
  const rail = useRailState();
  const { data: requests, error, isLoading } = useReviewAssistantRequests(projectId);
  const [selection, setSelection] = useState<Selection | null>(null);

  if (error) return <TabError what="your requests" error={error} />;
  if (isLoading || !requests) return <TabLoading label="Loading requests..." />;

  // Land on the newest request when there is one, and on the composer otherwise.
  const shown: Selection =
    selection ?? (requests[0] ? { kind: 'request', runId: requests[0].run.id } : { kind: 'new' });
  const selected = shown.kind === 'request' ? requests.find((request) => request.run.id === shown.runId) : undefined;
  const select = (next: Selection) => {
    setSelection(next);
    rail.close();
  };

  return (
    <div className="flex h-full min-h-0">
      <Rail state={rail} label="Requests">
        <RequestRail
          requests={requests}
          selection={shown}
          readOnly={readOnly}
          onNew={() => select({ kind: 'new' })}
          onSelect={(runId) => select({ kind: 'request', runId })}
        />
      </Rail>

      <main className="flex min-w-0 flex-1 flex-col">
        <div className="flex h-10 shrink-0 items-center gap-2 border-b px-2">
          <RailToggle state={rail} label="Requests" />
          <span className="min-w-0 truncate text-xs text-muted-foreground">
            {selected ? requestBarLabel(selected) : 'New request'}
          </span>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto">
          <div className="mx-auto max-w-5xl px-6 py-5 md:px-10">
            {shown.kind === 'new' || !selected ? (
              readOnly ? (
                <p className="text-sm text-muted-foreground">No requests yet.</p>
              ) : (
                <RequestComposer overview={overview} onStarted={(runId) => setSelection({ kind: 'request', runId })} />
              )
            ) : (
              <RequestView
                key={selected.run.id}
                projectId={projectId}
                request={selected}
                projectFiles={overview.files ?? []}
                readOnly={readOnly}
              />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

const plural = (count: number, noun: string) => `${count} ${noun}${count === 1 ? '' : 's'}`;

/**
 * The bar above a request: what went in and came out, and when it finished.
 * The heading below already names the outputs and when the request started.
 */
function requestBarLabel(request: ReviewAssistantRequestSummary): string {
  const shape = `${plural(request.outputs.length, 'output')} from ${plural(request.input_file_ids.length, 'document')}`;
  const { status, completed_at: completedAt } = request.run;
  if (isWorkflowProcessing({ run: request.run })) return `${shape} · in progress`;
  if (status === WorkflowRunStatus.Cancelled) return `${shape} · cancelled`;
  if (status === WorkflowRunStatus.Failed) return `${shape} · failed`;
  return completedAt ? `${shape} · finished ${format(new Date(completedAt), 'MMM d, h:mm a')}` : shape;
}

function RequestRail({
  requests,
  selection,
  readOnly,
  onNew,
  onSelect,
}: {
  requests: ReviewAssistantRequestSummary[];
  selection: Selection;
  readOnly: boolean;
  onNew: () => void;
  onSelect: (runId: string) => void;
}) {
  return (
    <div className="flex h-full flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto p-3">
        {!readOnly && (
          <button
            onClick={onNew}
            aria-current={selection.kind === 'new' ? 'page' : undefined}
            className={cn(
              'flex w-full cursor-pointer items-center gap-2 rounded-md px-2 py-2 text-left text-[13px] font-medium transition-colors',
              selection.kind === 'new' ? RAIL_ITEM_ACTIVE : RAIL_ITEM_IDLE,
            )}
          >
            <Plus className="size-3.5" />
            New request
          </button>
        )}

        <h2 className="mt-4 px-2 font-mono text-[10px] tracking-wide text-muted-foreground uppercase">Requests</h2>
        {requests.length === 0 ? (
          <p className="mt-2 px-2 text-xs text-muted-foreground">None yet.</p>
        ) : (
          <ul className="mt-2 space-y-px">
            {requests.map((request) => {
              const active = selection.kind === 'request' && selection.runId === request.run.id;
              return (
                <li key={request.run.id}>
                  <button
                    onClick={() => onSelect(request.run.id)}
                    aria-current={active ? 'page' : undefined}
                    className={cn(
                      'w-full cursor-pointer rounded-md px-2 py-2 text-left transition-colors',
                      active ? RAIL_ITEM_ACTIVE : RAIL_ITEM_IDLE,
                    )}
                  >
                    <span className="block text-[13px] leading-tight font-medium">
                      {request.outputs.map(outputTitle).join(', ')}
                    </span>
                    <span className="mt-1 flex items-center gap-2 text-[11px] text-muted-foreground">
                      <StatusIndicator status={getDisplayStatus(request)} />
                      {format(new Date(request.run.created_at), 'MMM d, h:mm a')}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <p className="shrink-0 border-t px-5 py-4 text-xs leading-relaxed text-muted-foreground">
        Pick the outputs you need, then add your drafts, reviewer memos, marked-up copies and response memos. The Review
        Assistant works out which is which. <HelpLink topic="review-assistant">More details</HelpLink>
      </p>
    </div>
  );
}
