'use client';

import { ActivityGranularity, ActivityPoint } from '@/lib/generated-api';
import { cn } from '@/lib/utils';
import { formatAxisLabel, formatBucketFull, formatBucketLabel, formatCompact } from './format';

type Granularity = 'day' | 'week';

interface Series {
  key: 'workflow_runs' | 'active_users' | 'projects_created';
  title: string;
  unit: string;
  /**
   * False where the buckets must not be summed: active users is a distinct
   * count per bucket, so adding the buckets up would count returning users
   * once per day they showed up.
   */
  additive: boolean;
}

const SERIES: Series[] = [
  { key: 'workflow_runs', title: 'Assessments run', unit: 'runs', additive: true },
  { key: 'active_users', title: 'Active users', unit: 'users', additive: false },
  { key: 'projects_created', title: 'Projects created', unit: 'projects', additive: true },
];

/**
 * One bucketed column chart.
 *
 * The three series live in separate charts rather than one plot: runs are
 * counted in the hundreds and users in single digits, and a second y-axis to
 * fit them together would misstate both.
 */
function ColumnChart({
  title,
  points,
  granularity,
  unit,
  additive,
}: {
  title: string;
  points: { bucket: Date; value: number }[];
  granularity: Granularity;
  unit: string;
  additive: boolean;
}) {
  const max = Math.max(...points.map((point) => point.value), 1);
  const total = points.reduce((sum, point) => sum + point.value, 0);
  const peak = points.reduce((best, point) => (point.value > best.value ? point : best), points[0]);

  return (
    <div className="min-w-0">
      <div className="flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-medium text-foreground">{title}</h3>
        <span className="text-xs text-muted-foreground tabular-nums">
          {additive ? `${formatCompact(total)} total` : `distinct per ${granularity}`}
        </span>
      </div>
      <p className="mt-0.5 text-xs text-muted-foreground">
        {peak && peak.value > 0
          ? `Peak ${formatCompact(peak.value)} ${unit} · ${granularity === 'week' ? 'week of ' : ''}${formatBucketLabel(peak.bucket)}`
          : `No ${unit} in this period`}
      </p>

      <div
        className="mt-3 flex h-28 items-end gap-0.5"
        role="img"
        aria-label={`${title} per ${granularity}. ${formatCompact(total)} ${unit} in total.`}
      >
        {points.map((point, index) => {
          const alignment =
            index < points.length * 0.15
              ? 'left-0'
              : index > points.length * 0.85
                ? 'right-0'
                : 'left-1/2 -translate-x-1/2';
          // Percentage of the plot height, reused to sit the tooltip on the bar's cap.
          const height = point.value === 0 ? '0px' : `max(2px, ${(point.value / max) * 100}%)`;
          return (
            <div key={String(point.bucket)} className="group relative flex h-full flex-1 items-end" tabIndex={0}>
              {/*
                The strip spans the full plot width so the bars stay under the
                axis line and its end labels; the bar itself is capped and
                centred inside it. A few wide buckets must not turn into slabs,
                and the strip stays the hover target so thin bars keep a
                reachable hit area.
              */}
              <div className="mx-auto w-full max-w-6 rounded-t bg-[var(--viz-series-1)]" style={{ height }} />
              <div
                className={cn(
                  'pointer-events-none absolute z-20 hidden whitespace-nowrap rounded-md border border-border bg-popover px-2 py-1 text-xs text-popover-foreground shadow-md group-hover:block group-focus-within:block',
                  alignment,
                )}
                style={{ bottom: `calc(${height} + 4px)` }}
              >
                <span className="font-medium">{formatCompact(point.value)}</span> {unit}
                <span className="text-muted-foreground"> · {formatBucketFull(point.bucket, granularity)}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-1.5 flex justify-between border-t border-[var(--viz-grid)] pt-1.5 text-xs text-muted-foreground">
        <span>{points.length > 0 && formatAxisLabel(points[0].bucket, granularity)}</span>
        <span>{points.length > 0 && formatAxisLabel(points[points.length - 1].bucket, granularity)}</span>
      </div>
    </div>
  );
}

export function ActivityCharts({
  activity,
  granularity,
}: {
  activity: ActivityPoint[];
  granularity: ActivityGranularity;
}) {
  const bucketUnit: Granularity = granularity === ActivityGranularity.Week ? 'week' : 'day';

  return (
    <div className="space-y-4">
      {/*
        Each series is its own panel, divided by a hairline: three plots sharing
        a row read as one chart with three groups otherwise, and they have
        neither a shared axis nor a shared scale. The rule turns into a
        horizontal one once the panels stack.
      */}
      <div className="grid gap-6 md:grid-cols-3">
        {SERIES.map((series, index) => (
          <div
            key={series.key}
            className={cn(
              'min-w-0',
              index > 0 && 'border-t border-border pt-6 md:border-t-0 md:border-l md:pt-0 md:pl-6',
            )}
          >
            <ColumnChart
              title={series.title}
              unit={series.unit}
              additive={series.additive}
              granularity={bucketUnit}
              points={activity.map((point) => ({ bucket: point.bucket, value: point[series.key] }))}
            />
          </div>
        ))}
      </div>

      <details className="group">
        <summary className="w-fit cursor-pointer text-xs text-muted-foreground hover:text-foreground">
          Show activity data
        </summary>
        <div className="mt-2 max-h-64 overflow-y-auto rounded-md border border-border">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-muted text-xs text-muted-foreground">
              <tr>
                <th className="px-3 py-2 text-left font-medium">{bucketUnit === 'week' ? 'Week of' : 'Day'}</th>
                {SERIES.map((series) => (
                  <th key={series.key} className="px-3 py-2 text-right font-medium">
                    {series.title}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {activity.map((point) => (
                <tr key={String(point.bucket)} className="border-t border-border">
                  <td className="px-3 py-1.5">{formatBucketFull(point.bucket, bucketUnit)}</td>
                  {SERIES.map((series) => (
                    <td key={series.key} className="px-3 py-1.5 text-right tabular-nums">
                      {point[series.key].toLocaleString('en-US')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
