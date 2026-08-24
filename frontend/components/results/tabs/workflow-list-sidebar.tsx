'use client';

import { IssueCountBadge } from '@/components/results/components/issue-count-badge';
import { Button } from '@/components/ui/button';
import { StatusIndicator } from '@/components/ui/status-indicator';
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
import { formatDistanceToNow } from 'date-fns';
import { AlertTriangleIcon, ChevronDownIcon, InfoIcon, PlusIcon, XCircleIcon } from 'lucide-react';
import { useState } from 'react';

interface WorkflowListItemProps {
  workflowDetail: WorkflowRunDetail;
  issues: Issue[];
  isSelected: boolean;
  onSelect: () => void;
}

function WorkflowListItem({ workflowDetail, issues, isSelected, onSelect }: WorkflowListItemProps) {
  const displayStatus = getDisplayStatus(workflowDetail);
  const hasErrors = hasBlockingErrors(workflowDetail);
  // Recovered failures: the run completed, so flag them without the error tone.
  const hasWarnings = !hasErrors && hasCurrentRunErrors(workflowDetail);
  const hasFailed = isWorkflowFailed(workflowDetail);
  const failureMessage = workflowDetail.run.failure_message;
  const { getWorkflowTypeName } = useWorkflowTypes();
  // A run still working has nothing final to count, so no badge until it settles.
  const issuesSummary = isWorkflowProcessing(workflowDetail)
    ? null
    : summarizeReportedIssues(issues, workflowDetail.run.type);

  return (
    <button
      onClick={onSelect}
      className={cn(
        'w-full text-left p-3 rounded-lg border transition-colors hover:bg-muted/50 cursor-pointer shadow-xs',
        isSelected && 'bg-muted border-primary shadow',
      )}
    >
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2 font-medium text-sm">
          {getWorkflowTypeName(workflowDetail.run.type)}
          {hasErrors && (
            <Tooltip>
              <TooltipTrigger asChild>
                <AlertTriangleIcon className="w-4 h-4 text-destructive cursor-help" />
              </TooltipTrigger>
              <TooltipContent>This workflow completed with errors. Please check them and try again.</TooltipContent>
            </Tooltip>
          )}
          {hasWarnings && (
            <Tooltip>
              <TooltipTrigger asChild>
                <AlertTriangleIcon className="w-4 h-4 text-amber-600 cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                This workflow completed, but some parts returned incomplete results. Check the details in its results.
              </TooltipContent>
            </Tooltip>
          )}
          {hasFailed && (
            <Tooltip>
              <TooltipTrigger asChild>
                <XCircleIcon className="w-4 h-4 text-destructive cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                {failureMessage ?? 'This workflow failed before it could complete. Please retry it.'}
              </TooltipContent>
            </Tooltip>
          )}
          {issuesSummary && (
            <span className="ml-auto pl-2">
              <IssueCountBadge summary={issuesSummary} />
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 justify-between">
          <div className="text-xs text-muted-foreground">
            {formatDistanceToNow(workflowDetail.run.last_updated_at, { addSuffix: true })}
          </div>
          <StatusIndicator status={displayStatus} />
        </div>
      </div>
    </button>
  );
}

interface WorkflowListSidebarProps {
  workflowDetails: WorkflowRunDetail[];
  issues: Issue[];
  selectedWorkflowType: WorkflowRunType | null;
  onSelectWorkflowType: (type: WorkflowRunType) => void;
  onStartNewAnalysis: () => void;
  readOnly?: boolean;
}

export function WorkflowListSidebar({
  workflowDetails,
  issues,
  selectedWorkflowType,
  onSelectWorkflowType,
  onStartNewAnalysis,
  readOnly,
}: WorkflowListSidebarProps) {
  const { isWorkflowTypeVisible } = useWorkflowTypes();
  const [internalExpanded, setInternalExpanded] = useState(false);

  const visibleWorkflows = workflowDetails.filter((wd) => isWorkflowTypeVisible(wd.run.type));
  const internalWorkflows = workflowDetails.filter((wd) => !isWorkflowTypeVisible(wd.run.type));

  return (
    <div className="w-1/4 overflow-y-auto border-r pr-4">
      <div className="space-y-2">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold">Assessments</h3>
          {!readOnly && (
            <Button size="xs" variant="outline" onClick={onStartNewAnalysis}>
              <PlusIcon className="size-3" />
              New Assessment
            </Button>
          )}
        </div>
        {visibleWorkflows.map((workflowDetail) => (
          <WorkflowListItem
            key={workflowDetail.run.id}
            workflowDetail={workflowDetail}
            issues={issues}
            isSelected={selectedWorkflowType === workflowDetail.run.type}
            onSelect={() => onSelectWorkflowType(workflowDetail.run.type)}
          />
        ))}
        {internalWorkflows.length > 0 && (
          <div className="pt-4">
            <button
              onClick={() => setInternalExpanded((prev) => !prev)}
              className="flex items-center gap-1 mb-2 w-full text-left group cursor-pointer"
            >
              <ChevronDownIcon
                className={cn('w-3 h-3 text-muted-foreground transition-transform', !internalExpanded && '-rotate-90')}
              />
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide group-hover:text-foreground transition-colors">
                Internal Workflows
              </h4>
              <span className="text-xs text-muted-foreground font-normal">({internalWorkflows.length})</span>
              <Tooltip>
                <TooltipTrigger asChild>
                  <InfoIcon
                    className="w-3 h-3 text-muted-foreground cursor-help ml-1"
                    onClick={(e) => e.stopPropagation()}
                  />
                </TooltipTrigger>
                <TooltipContent>
                  These workflows run automatically as part of the analysis pipeline and are not user-triggered.
                </TooltipContent>
              </Tooltip>
            </button>
            {internalExpanded && (
              <div className="space-y-2">
                {internalWorkflows.map((workflowDetail) => (
                  <div key={workflowDetail.run.id} className="opacity-70">
                    <WorkflowListItem
                      workflowDetail={workflowDetail}
                      issues={issues}
                      isSelected={selectedWorkflowType === workflowDetail.run.type}
                      onSelect={() => onSelectWorkflowType(workflowDetail.run.type)}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
