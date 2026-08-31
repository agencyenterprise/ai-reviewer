'use client';

import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Switch } from '@/components/ui/switch';
import { WorkflowUsageItem } from '@/lib/generated-api';
import { useState } from 'react';
import { formatDuration, formatPercent } from './format';

/**
 * Runs, outcomes, speed and feedback per workflow type.
 *
 * Internal (dependency) and retired workflows are hidden by default: they are
 * real runs, but neither is something a user picked in this period.
 */
export function AssessmentsTable({ workflows }: { workflows: WorkflowUsageItem[] }) {
  const [showAll, setShowAll] = useState(false);
  const current = workflows.filter((workflow) => !workflow.is_internal && !workflow.is_retired);
  const rows = showAll ? workflows : current;
  const hiddenCount = workflows.length - current.length;

  return (
    <div className="space-y-3">
      <label className="flex w-fit items-center gap-2 text-sm text-muted-foreground">
        <Switch checked={showAll} onCheckedChange={setShowAll} />
        Include internal and retired workflows ({hiddenCount})
      </label>

      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">Nothing ran in this period.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Assessment</TableHead>
              <TableHead className="text-right">Runs</TableHead>
              <TableHead className="text-right">Completed</TableHead>
              <TableHead className="text-right">Failed</TableHead>
              <TableHead className="text-right">Median time</TableHead>
              <TableHead className="text-right">Feedback</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((workflow) => (
              <TableRow key={workflow.type}>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{workflow.name}</span>
                    {workflow.is_internal && <Badge variant="secondary">Internal</Badge>}
                    {workflow.is_retired && <Badge variant="outline">Retired</Badge>}
                  </div>
                  <span className="text-xs text-muted-foreground">{workflow.type}</span>
                </TableCell>
                <TableCell className="text-right tabular-nums">{workflow.runs.toLocaleString('en-US')}</TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatPercent(workflow.statuses.completed / workflow.runs)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {workflow.statuses.failed > 0 ? (
                    <span className="text-[var(--viz-critical)]">
                      {workflow.statuses.failed.toLocaleString('en-US')}
                    </span>
                  ) : (
                    <span className="text-muted-foreground">0</span>
                  )}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatDuration(workflow.median_duration_seconds)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {workflow.thumbs_up + workflow.thumbs_down === 0 ? (
                    <span className="text-muted-foreground">—</span>
                  ) : (
                    <span>
                      <span className="text-[var(--viz-good)]">{workflow.thumbs_up}</span>
                      <span className="text-muted-foreground"> / </span>
                      <span className="text-[var(--viz-critical)]">{workflow.thumbs_down}</span>
                    </span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
