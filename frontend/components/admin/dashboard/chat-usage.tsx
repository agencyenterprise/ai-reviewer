'use client';

import { ActivityGranularity, ChatActivityPoint, ChatSurfaceUsage, ConversationKind } from '@/lib/generated-api';
import { cn } from '@/lib/utils';
import { ColumnChart } from './activity-charts';
import { StatTile } from './stat-tile';

const SURFACE_LABELS: Record<ConversationKind, string> = {
  [ConversationKind.Web]: 'Web chat',
  [ConversationKind.Word]: 'Word add-in',
  [ConversationKind.Teams]: 'Teams',
};

function hint(surface: ChatSurfaceUsage): string {
  const started = surface.conversations_started.current.toLocaleString('en-US');
  const people = surface.people.toLocaleString('en-US');
  return `${started} new conversations · ${people} ${surface.people === 1 ? 'person' : 'people'}`;
}

/**
 * Messages people sent to Draft Detective, one column per surface.
 *
 * One chart per surface rather than a stacked one, as for the activity
 * charts: the web chat can outnumber Teams many times over, and a shared
 * scale would flatten the smaller surfaces into nothing.
 */
export function ChatUsage({
  surfaces,
  activity,
  granularity,
  comparisonLabel,
}: {
  surfaces: ChatSurfaceUsage[];
  activity: ChatActivityPoint[];
  granularity: ActivityGranularity;
  comparisonLabel: string;
}) {
  const bucketUnit = granularity === ActivityGranularity.Week ? 'week' : 'day';

  return (
    <div className="grid gap-6 md:grid-cols-3">
      {surfaces.map((surface, index) => (
        <div
          key={surface.surface}
          className={cn(
            'min-w-0 space-y-4',
            index > 0 && 'border-t border-border pt-6 md:border-t-0 md:border-l md:pt-0 md:pl-6',
          )}
        >
          <StatTile
            label={`${SURFACE_LABELS[surface.surface]} messages`}
            value={surface.messages.current}
            previous={surface.messages.previous}
            comparisonLabel={comparisonLabel}
            hint={hint(surface)}
          />
          <ColumnChart
            title={`Per ${bucketUnit}`}
            unit="messages"
            additive
            granularity={bucketUnit}
            points={activity.map((point) => ({ bucket: point.bucket, value: point[surface.surface] }))}
          />
        </div>
      ))}
    </div>
  );
}
