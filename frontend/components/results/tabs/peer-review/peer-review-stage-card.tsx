'use client';

import { Button } from '@/components/ui/button';
import { Callout } from '@/components/ui/callout';
import { StatusIndicator } from '@/components/ui/status-indicator';
import { TabsTrigger } from '@/components/ui/tabs';
import { WorkflowRunDetail, WorkflowRunStatus } from '@/lib/generated-api';
import { cn } from '@/lib/utils';
import { getDisplayStatus, isWorkflowProcessing } from '@/lib/workflow-state';
import { Check, Info, Loader2, X, type LucideIcon } from 'lucide-react';
import { ReactNode } from 'react';

interface StepTriggerProps {
  value: string;
  index: number;
  title: string;
  /** One line describing what this step does. */
  subtitle: string;
  complete: boolean;
  blocked: boolean;
  /** The run backing this step's status chip. Absent for steps the author does by hand. */
  run?: WorkflowRunDetail;
  /** Status text when the step is actionable but not yet done. */
  readyLabel?: string;
}

/**
 * One step, rendered as a clickable card that behaves as a tab.
 *
 * These reports run to many screens, so the steps select a single panel rather
 * than stacking: only the active step's report is mounted, and switching
 * between them does not mean scrolling past the others.
 */
export function PeerReviewStepTrigger({
  value,
  index,
  title,
  subtitle,
  complete,
  blocked,
  run,
  readyLabel = 'Ready to run',
}: StepTriggerProps) {
  return (
    <TabsTrigger
      value={value}
      className={cn(
        // Override the pill-style defaults: these are full cards in a grid.
        // `border-border` is required — the default sets `border-transparent`,
        // which is a colour class and so survives adding `border`.
        'h-auto w-full flex-none items-start justify-start whitespace-normal rounded-lg border border-border bg-card p-3 text-left shadow-none',
        'data-[state=active]:border-primary data-[state=active]:bg-accent/50 data-[state=active]:shadow-sm',
        // The default carries a dark-mode active border that would otherwise
        // win over the one above, since it is a different variant.
        'dark:data-[state=active]:border-primary dark:data-[state=active]:bg-accent/30',
        'hover:bg-accent/30',
      )}
    >
      <div className="flex w-full items-start gap-3">
        <span
          className={cn(
            'flex size-6 shrink-0 items-center justify-center rounded-full border text-xs font-medium',
            complete
              ? 'border-green-600 bg-green-600 text-white'
              : blocked
                ? 'border-muted-foreground/30 text-muted-foreground'
                : 'border-primary text-primary',
          )}
        >
          {complete ? <Check className="size-3.5" /> : index}
        </span>
        <div className="min-w-0 flex-1 space-y-1">
          <div className="text-sm font-medium leading-tight">{title}</div>
          <div className="text-xs font-normal text-muted-foreground leading-snug">{subtitle}</div>
          <div className="pt-0.5">
            {/* A run's own status wins. Steps the author does by hand have no
                run, so completion has to be reported from `complete` — without
                this they show a tick and "Ready to run" at the same time. */}
            {run ? (
              <StatusIndicator status={getDisplayStatus(run)} />
            ) : complete ? (
              <StatusIndicator status={WorkflowRunStatus.Completed} />
            ) : (
              <span className="text-xs text-muted-foreground">{blocked ? 'Not ready' : readyLabel}</span>
            )}
          </div>
        </div>
      </div>
    </TabsTrigger>
  );
}

interface StagePanelProps {
  /** Non-null when the step cannot be acted on; rendered above the body. */
  blockedReason: string | null;
  actions?: ReactNode;
  children?: ReactNode;
}

/**
 * Body of the selected step: why it is blocked, its content, then its actions.
 *
 * Deliberately unbordered. The step card above is highlighted while its panel is
 * open, which is what identifies the selection, and this content already sits
 * inside the bordered tab container — a border here would nest a box in a box
 * around reports that carry their own framing.
 */
export function PeerReviewStagePanel({ blockedReason, actions, children }: StagePanelProps) {
  return (
    <div className="space-y-4">
      {blockedReason && (
        <Callout variant="info" icon={Info} title="Not ready yet">
          <p className="text-sm">{blockedReason}</p>
        </Callout>
      )}
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
      {children}
    </div>
  );
}

/**
 * The call to action for a step with nothing to show yet: what it produces,
 * then the button. Centred like `EmptyState`, but with a dashed border of its
 * own rather than a Card: the stage panel around it is unbordered, and an empty
 * step needs to read as a target rather than as text floating in the tab.
 */
export function PeerReviewStageCta({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-lg border border-dashed px-6 py-10 text-center">
      <Icon className="size-8 text-muted-foreground" />
      <div className="space-y-1.5">
        <p className="text-sm font-medium">{title}</p>
        <p className="mx-auto max-w-prose text-sm text-muted-foreground">{description}</p>
      </div>
      {action}
    </div>
  );
}

interface StageActionProps {
  label: string;
  /** Overrides the "Re-run" text when a result already exists. */
  reRunLabel?: string;
  run?: WorkflowRunDetail;
  disabled: boolean;
  isStarting: boolean;
  variant?: 'default' | 'outline';
  /** CTA buttons render at the default size; toolbar ones stay small. */
  size?: 'sm' | 'default';
  onStart: () => void;
  onCancel: (runId: string) => void;
}

/**
 * Start / cancel / re-run for one deliverable.
 *
 * Not `StartWorkflowButton`: that opens `WorkflowConfigDialog`, the dialog this
 * tab exists to remove, and none of these workflows needs web-search consent or
 * a publication date, so there is nothing to configure.
 */
export function PeerReviewStageAction({
  label,
  reRunLabel,
  run,
  disabled,
  isStarting,
  variant = 'default',
  size = 'sm',
  onStart,
  onCancel,
}: StageActionProps) {
  if (run && isWorkflowProcessing(run)) {
    return (
      <Button variant="outline" size={size} onClick={() => onCancel(run.run.id)}>
        <Loader2 className="size-4 animate-spin" />
        Running
        <X className="size-4" />
      </Button>
    );
  }

  const hasResult = !!run;
  return (
    <Button variant={hasResult ? 'outline' : variant} size={size} disabled={disabled || isStarting} onClick={onStart}>
      {isStarting && <Loader2 className="size-4 animate-spin" />}
      {hasResult ? (reRunLabel ?? 'Re-run') : label}
    </Button>
  );
}
