'use client';

import { HelpLink } from '@/components/help/help-link';
import { StatusIndicator } from '@/components/ui/status-indicator';
import { WorkflowRunStatus } from '@/lib/generated-api';
import { cn } from '@/lib/utils';
import { getDisplayStatus } from '@/lib/workflow-state';
import { Check } from 'lucide-react';
import { STEPS, StepId, StepState } from './steps';

interface StepRailProps {
  states: Record<StepId, StepState>;
  activeStep: StepId;
  onSelectStep: (step: StepId) => void;
}

/**
 * The four steps as a stepper. Peer review is the one tab that is a sequence
 * rather than a set, so the rail numbers its rows and marks the ones already
 * done — where the other tabs' rails just list what exists.
 */
export function StepRail({ states, activeStep, onSelectStep }: StepRailProps) {
  return (
    <div className="flex h-full flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto p-3">
        <h2 className="px-2 font-mono text-[10px] tracking-wide text-muted-foreground uppercase">Steps</h2>

        <ol className="mt-2 space-y-px">
          {STEPS.map((step, index) => {
            const state = states[step.id];
            const active = activeStep === step.id;
            return (
              <li key={step.id}>
                <button
                  onClick={() => onSelectStep(step.id)}
                  aria-current={active ? 'step' : undefined}
                  className={cn(
                    'flex w-full cursor-pointer gap-2.5 rounded-md px-2 py-2 text-left transition-colors',
                    active ? 'bg-accent text-accent-foreground' : 'hover:bg-accent/60',
                  )}
                >
                  <StepMarker index={index + 1} complete={state.complete} blocked={state.blockedReason !== null} />
                  <span className="min-w-0 flex-1">
                    <span className="block text-[13px] leading-tight font-medium">{step.title}</span>
                    <span className="mt-1 block">
                      {/* A run's own status wins. The upload step has no run, so
                          its completion has to come from the facts instead. */}
                      {state.run ? (
                        <StatusIndicator status={getDisplayStatus(state.run)} />
                      ) : state.complete ? (
                        <StatusIndicator status={WorkflowRunStatus.Completed} />
                      ) : (
                        <span className="text-[11px] text-muted-foreground">
                          {state.blockedReason ? 'Not ready' : 'Ready to run'}
                        </span>
                      )}
                    </span>
                  </span>
                </button>
              </li>
            );
          })}
        </ol>
      </div>

      <p className="shrink-0 border-t px-5 py-4 text-xs leading-relaxed text-muted-foreground">
        Reviewer memos are documents peer reviewers wrote about your draft. These four steps read them, help you plan
        and write the revision, and then report how fully each point was addressed.{' '}
        <HelpLink topic="peer-review">More details</HelpLink>
      </p>
    </div>
  );
}

function StepMarker({ index, complete, blocked }: { index: number; complete: boolean; blocked: boolean }) {
  if (complete) {
    return (
      <span className="mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full bg-green-600 dark:bg-green-500">
        <Check className="size-2.5 text-white" strokeWidth={3} />
      </span>
    );
  }

  return (
    <span
      className={cn(
        'mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full border text-[9px] font-medium',
        blocked ? 'border-muted-foreground/30 text-muted-foreground' : 'border-primary text-primary',
      )}
    >
      {index}
    </span>
  );
}
