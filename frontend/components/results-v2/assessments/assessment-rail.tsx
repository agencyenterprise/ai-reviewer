'use client';

import { HelpLink } from '@/components/help/help-link';
import { IssueCountBadge } from '@/components/results/components/issue-count-badge';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Issue, WorkflowRunDetail, WorkflowRunType } from '@/lib/generated-api';
import { summarizeReportedIssues } from '@/lib/health-status';
import { useWorkflowTypes } from '@/lib/hooks/use-workflow-types';
import { cn } from '@/lib/utils';
import {
  getDisplayStatus,
  hasBlockingErrors,
  hasCurrentRunErrors,
  isWorkflowFailed,
  isWorkflowProcessing,
} from '@/lib/workflow-state';
import { AlertTriangleIcon, ChevronDownIcon, Loader2, XCircleIcon } from 'lucide-react';
import { useState } from 'react';

/** The dot that carries a run's state, in the palette the status indicator uses. */
const STATUS_DOT: Record<string, string> = {
  completed: 'bg-green-500',
  running: 'bg-primary animate-pulse',
  pending: 'bg-muted-foreground/40',
  failed: 'bg-red-500',
  cancelled: 'bg-muted-foreground/40',
  awaiting_approval: 'bg-amber-500',
};

interface AssessmentRailProps {
  workflowDetails: WorkflowRunDetail[];
  issues: Issue[];
  selectedWorkflowType: WorkflowRunType | null;
  onSelectWorkflowType: (type: WorkflowRunType) => void;
  onStartNewAssessment: () => void;
  readOnly: boolean;
}

/**
 * The assessment list, which in this tab is the navigation rather than a
 * filter: picking one is what fills the pane beside it. Internal workflows
 * stay folded away — they run themselves, and nobody reads their results
 * unless something has gone wrong.
 */
export function AssessmentRail({
  workflowDetails,
  issues,
  selectedWorkflowType,
  onSelectWorkflowType,
  onStartNewAssessment,
  readOnly,
}: AssessmentRailProps) {
  const { isWorkflowTypeVisible } = useWorkflowTypes();
  const [internalOpen, setInternalOpen] = useState(false);

  const visible = workflowDetails.filter((detail) => isWorkflowTypeVisible(detail.run.type));
  const internal = workflowDetails.filter((detail) => !isWorkflowTypeVisible(detail.run.type));

  return (
    <div className="flex h-full flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto p-3">
        <div className="flex items-center justify-between px-2">
          <h2 className="font-mono text-[10px] tracking-wide text-muted-foreground uppercase">Assessments</h2>
          {!readOnly && (
            <Button variant="link" size="sm" className="h-auto p-0 text-xs" onClick={onStartNewAssessment}>
              Run more
            </Button>
          )}
        </div>

        <div className="mt-2 space-y-px">
          {visible.map((detail) => (
            <AssessmentRow
              key={detail.run.id}
              detail={detail}
              issues={issues}
              active={selectedWorkflowType === detail.run.type}
              onSelect={() => onSelectWorkflowType(detail.run.type)}
            />
          ))}
        </div>

        {internal.length > 0 && (
          <div className="mt-4">
            <button
              onClick={() => setInternalOpen(!internalOpen)}
              aria-expanded={internalOpen}
              className="group flex w-full cursor-pointer items-center gap-1 px-2 text-left"
            >
              <ChevronDownIcon
                className={cn('size-3 text-muted-foreground transition-transform', !internalOpen && '-rotate-90')}
              />
              <h3 className="font-mono text-[10px] tracking-wide text-muted-foreground uppercase group-hover:text-foreground">
                Pipeline steps
              </h3>
              <span className="font-mono text-[10px] text-muted-foreground">{internal.length}</span>
            </button>
            {internalOpen && (
              <>
                <p className="mt-1.5 px-2 text-[11px] leading-relaxed text-muted-foreground">
                  These run on their own to prepare the document. You never start them.
                </p>
                <div className="mt-1.5 space-y-px">
                  {internal.map((detail) => (
                    <AssessmentRow
                      key={detail.run.id}
                      detail={detail}
                      issues={issues}
                      active={selectedWorkflowType === detail.run.type}
                      onSelect={() => onSelectWorkflowType(detail.run.type)}
                    />
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      <p className="shrink-0 border-t px-5 py-4 text-xs leading-relaxed text-muted-foreground">
        Each assessment reads the document once and reports what it finds. Those findings are the issues the document
        explorer marks up. <HelpLink topic="assessments">More details</HelpLink>
      </p>
    </div>
  );
}

function AssessmentRow({
  detail,
  issues,
  active,
  onSelect,
}: {
  detail: WorkflowRunDetail;
  issues: Issue[];
  active: boolean;
  onSelect: () => void;
}) {
  const { getWorkflowTypeName } = useWorkflowTypes();
  const processing = isWorkflowProcessing(detail);
  const status = getDisplayStatus(detail);
  const errored = hasBlockingErrors(detail);
  // A recovered failure: the run finished, so flag it without the error tone.
  const warned = !errored && hasCurrentRunErrors(detail);
  const failed = isWorkflowFailed(detail);
  // A run still working has nothing final to count.
  const summary = processing ? null : summarizeReportedIssues(issues, detail.run.type);

  return (
    <button
      onClick={onSelect}
      aria-pressed={active}
      className={cn(
        'flex w-full cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors',
        active ? 'bg-accent text-accent-foreground font-medium' : 'hover:bg-accent/60',
      )}
    >
      {processing ? (
        <Loader2 className="text-primary size-3 shrink-0 animate-spin" />
      ) : (
        <span className={cn('block size-2 shrink-0 rounded-full', STATUS_DOT[status] ?? 'bg-muted-foreground/40')} />
      )}

      <span className="flex-1 truncate">{getWorkflowTypeName(detail.run.type)}</span>

      {failed && (
        <FlagIcon
          tone="error"
          message={detail.run.failure_message ?? 'This assessment failed before it could finish. Try running it again.'}
        />
      )}
      {errored && !failed && (
        <FlagIcon tone="error" message="This assessment finished with errors. Check them and run it again." />
      )}
      {warned && (
        <FlagIcon tone="warning" message="This assessment finished, but parts of it returned incomplete results." />
      )}

      {summary && <IssueCountBadge summary={summary} />}
    </button>
  );
}

function FlagIcon({ tone, message }: { tone: 'error' | 'warning'; message: string }) {
  const Icon = tone === 'error' ? XCircleIcon : AlertTriangleIcon;
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        {/* A button rather than the icon itself: `asChild` would make the SVG
            the trigger, and an SVG takes no focus, so the explanation would be
            hover-only. */}
        <button type="button" aria-label={message} className="inline-flex shrink-0 cursor-help">
          <Icon className={cn('size-3.5', tone === 'error' ? 'text-destructive' : 'text-amber-600')} />
        </button>
      </TooltipTrigger>
      <TooltipContent className="max-w-xs">{message}</TooltipContent>
    </Tooltip>
  );
}
