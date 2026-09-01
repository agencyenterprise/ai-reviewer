'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { getDashboardApiAdminDashboardGet } from '@/lib/generated-api';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { Loader2 } from 'lucide-react';
import { useState } from 'react';
import { ActivityCharts } from './activity-charts';
import { AssessmentUsage } from './assessment-usage';
import { AssessmentsTable } from './assessments-table';
import { RunOutcomes } from './run-outcomes';
import { formatCacheWindow, toDate } from './format';
import { StatTile } from './stat-tile';
import { TopUsersTable } from './top-users-table';

const RANGES = [
  { days: 7, label: '7 days' },
  { days: 30, label: '30 days' },
  { days: 90, label: '90 days' },
  { days: 365, label: '12 months' },
] as const;

const DEFAULT_DAYS = 30;

export function UsageDashboard() {
  const [days, setDays] = useState<number>(DEFAULT_DAYS);

  const { data, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['admin', 'dashboard', days],
    queryFn: () => getDashboardApiAdminDashboardGet({ query: { days } }),
  });

  const rangeLabel = RANGES.find((range) => range.days === days)?.label ?? `${days} days`;
  const comparisonLabel = `previous ${rangeLabel}`;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Usage</h1>
          <p className="text-sm text-muted-foreground">How Draft Detective is being used over the last {rangeLabel}</p>
          {data && (
            <p className="mt-0.5 text-xs text-muted-foreground">
              As of {format(toDate(data.period_end), 'MMM d, HH:mm')} · figures refresh at most every{' '}
              <Tooltip>
                <TooltipTrigger asChild>
                  <span tabIndex={0} className="cursor-help underline decoration-dotted underline-offset-2">
                    {formatCacheWindow(data.cache_ttl_seconds)}
                  </span>
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  These figures are aggregated across every project and run, so they are computed at most once every{' '}
                  {formatCacheWindow(data.cache_ttl_seconds)} and served from a cache in between. A run that finished
                  moments ago can take that long to show up here.
                </TooltipContent>
              </Tooltip>
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isFetching && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
          <ToggleGroup
            type="single"
            value={String(days)}
            onValueChange={(value) => value && setDays(Number(value))}
            variant="outline"
            size="sm"
            className="bg-background shadow-xs"
          >
            {RANGES.map((range) => (
              <ToggleGroupItem key={range.days} value={String(range.days)} className="cursor-pointer px-3 text-xs">
                {range.label}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="py-16 text-center">
          <p className="text-destructive">{error.message}</p>
          <Button variant="outline" className="mt-4" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      ) : data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatTile
              label="Active users"
              value={data.active_users.current}
              previous={data.active_users.previous}
              comparisonLabel={comparisonLabel}
              hint={`${data.total_users.toLocaleString('en-US')} registered · ${data.new_users.current.toLocaleString('en-US')} new`}
            />
            <StatTile
              label="Assessments run"
              value={data.assessments_run.current}
              previous={data.assessments_run.previous}
              comparisonLabel={comparisonLabel}
              hint="Workflows a user chose to run"
            />
            <StatTile
              label="Projects created"
              value={data.projects_created.current}
              previous={data.projects_created.previous}
              comparisonLabel={comparisonLabel}
            />
            <StatTile
              label="Feedback shared"
              value={data.feedback_received.current}
              previous={data.feedback_received.previous}
              comparisonLabel={comparisonLabel}
              hint={`${data.feedback.thumbs_up} up · ${data.feedback.thumbs_down} down`}
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Activity</CardTitle>
              <CardDescription>
                Per {data.granularity}, over the last {rangeLabel}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ActivityCharts activity={data.activity} granularity={data.granularity} />
            </CardContent>
          </Card>

          <div className="grid gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Most used assessments</CardTitle>
                <CardDescription>Runs started in this period, share of all assessment runs</CardDescription>
              </CardHeader>
              <CardContent>
                <AssessmentUsage workflows={data.workflows} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Health</CardTitle>
                <CardDescription>Outcomes across every workflow, and how users rated the results</CardDescription>
              </CardHeader>
              <CardContent>
                <RunOutcomes workflows={data.workflows} feedback={data.feedback} />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Assessment detail</CardTitle>
              <CardDescription>
                Median time is measured over completed runs. Internal workflows run as dependencies of the assessments
                above.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AssessmentsTable workflows={data.workflows} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Most active users</CardTitle>
              <CardDescription>Top {data.top_users.length} by assessments run in this period</CardDescription>
            </CardHeader>
            <CardContent>
              <TopUsersTable users={data.top_users} />
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}
