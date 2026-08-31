'use client';

import { WorkflowUsageItem } from '@/lib/generated-api';
import { formatCompact, formatPercent } from './format';

const VISIBLE_ROWS = 8;

/**
 * Which assessments people actually reach for.
 *
 * Magnitude against a single scale, so one hue: the bar length carries the
 * comparison and the value sits at the tip. Retired types are left out — they
 * are no longer offered, so they cannot be reached for; the detail table below
 * still lists them.
 */
export function AssessmentUsage({ workflows }: { workflows: WorkflowUsageItem[] }) {
  const assessments = workflows.filter((workflow) => !workflow.is_internal && !workflow.is_retired);
  const rows = assessments.slice(0, VISIBLE_ROWS);
  const max = Math.max(...rows.map((row) => row.runs), 1);
  const total = assessments.reduce((sum, row) => sum + row.runs, 0);

  if (rows.length === 0) {
    return <p className="text-sm text-muted-foreground">No assessments were run in this period.</p>;
  }

  return (
    <div className="space-y-2.5">
      {rows.map((row) => (
        <div key={row.type} className="grid grid-cols-[minmax(0,11rem)_1fr] items-center gap-3">
          <span className="truncate text-sm text-foreground" title={row.name}>
            {row.name}
          </span>
          <div className="flex items-center gap-2">
            <div
              className="h-2.5 rounded-r bg-[var(--viz-series-1)]"
              style={{ width: `max(3px, ${(row.runs / max) * 100}%)` }}
            />
            <span className="shrink-0 text-xs tabular-nums text-foreground">{formatCompact(row.runs)}</span>
            <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
              {total > 0 && formatPercent(row.runs / total)}
            </span>
          </div>
        </div>
      ))}
      {assessments.length > rows.length && (
        <p className="pt-1 text-xs text-muted-foreground">{assessments.length - rows.length} more in the table below</p>
      )}
    </div>
  );
}
