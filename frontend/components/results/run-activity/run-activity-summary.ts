import { WorkflowRunPublic, WorkflowRunType } from '@/lib/generated-api';
import { isWorkflowProcessing } from '@/lib/workflow-state';
import { RunActivity, RunActivityItem } from './use-run-activity';

/**
 * How far along a run is, or null when it has no steps worth counting. A
 * single-step node has nothing to report but that it is going, and a bar pinned
 * at 0% or 100% would say something untrue about it.
 */
export function progressPercent(item: RunActivityItem): number | null {
  if (item.totalSteps <= 1) return null;
  return Math.min(100, Math.round((item.currentStep / item.totalSteps) * 100));
}

/**
 * What the Run assessments button says while work is going. Counts rather than
 * names, because the button keeps its width in the header; the names are in the
 * details popover beside it. One assessment adds its own progress, since past
 * one a single figure would blend runs that move at very different speeds.
 */
export function runActivityLabel({ running, queued }: RunActivity): string {
  if (running.length === 0) return queued.length > 0 ? `${queued.length} queued` : 'Starting…';
  if (running.length === 1) {
    const percent = progressPercent(running[0]);
    return percent !== null ? `Running · ${percent}%` : 'Running…';
  }
  return `Running ${running.length}…`;
}

/**
 * The same state for a screen reader, which has no spinner to see. The header
 * controls override their content with an aria-label, so this carries what the
 * label shows, a single run's progress included.
 */
export function runActivityStatus({ running, queued }: RunActivity): string {
  if (running.length === 0 && queued.length === 0) return 'Assessments starting';
  const percent = running.length === 1 ? progressPercent(running[0]) : null;
  const parts = [
    percent !== null
      ? `${running[0].label} ${percent}% done`
      : `${running.length} assessment${running.length === 1 ? '' : 's'} running`,
  ];
  if (queued.length > 0) parts.push(`${queued.length} queued`);
  return parts.join(', ');
}

/**
 * The assessments that cannot be started again right now: those with a run
 * working or queued, plus the ones just asked for whose runs the overview has
 * not caught up with yet. Starting one twice would only duplicate the work.
 */
export function busyWorkflowTypes(
  runs: { run: WorkflowRunPublic }[],
  starting: WorkflowRunType[] = [],
): WorkflowRunType[] {
  const busy = new Set(starting);
  for (const run of runs) {
    if (isWorkflowProcessing(run)) busy.add(run.run.type);
  }
  return Array.from(busy);
}
