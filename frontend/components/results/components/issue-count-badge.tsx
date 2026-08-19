'use client';

import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { SeverityEnum } from '@/lib/generated-api';
import { ReportedIssuesSummary } from '@/lib/health-status';
import { cn } from '@/lib/utils';
import {
  CheckCircleIcon,
  CircleAlertIcon,
  LucideProps,
  MessageCircleWarningIcon,
  TriangleAlertIcon,
} from 'lucide-react';

// Icons match SeverityBadge so a given severity reads the same across the app.
// Colours are foreground-only here: this sits inline with the assessment title,
// where a filled badge would shout over the title itself.
const severityDisplay: Record<
  SeverityEnum,
  { icon: React.ComponentType<LucideProps>; label: string; className: string }
> = {
  [SeverityEnum.None]: { icon: CheckCircleIcon, label: 'passing', className: 'text-green-700' },
  [SeverityEnum.Low]: { icon: MessageCircleWarningIcon, label: 'low', className: 'text-blue-600' },
  [SeverityEnum.Medium]: { icon: TriangleAlertIcon, label: 'medium', className: 'text-yellow-600' },
  [SeverityEnum.High]: { icon: CircleAlertIcon, label: 'high', className: 'text-red-600' },
};

/** Most severe first — the order the breakdown is read in. */
const REPORTED_TIERS = [SeverityEnum.High, SeverityEnum.Medium, SeverityEnum.Low];

/**
 * Compact count of the issues one assessment reported.
 *
 * Shows the size of the *most severe* tier rather than the total, so the colour
 * and the number always describe the same thing: "7 in red" means seven
 * high-severity issues, not thirty-four issues of which some are high. The full
 * breakdown is one hover away.
 */
export function IssueCountBadge({ summary }: { summary: ReportedIssuesSummary }) {
  const severity = summary.maxSeverity ?? SeverityEnum.None;
  const { icon: Icon, className } = severityDisplay[severity];
  const headline = summary.maxSeverity ? summary.counts[summary.maxSeverity] : 0;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          className={cn(
            'inline-flex shrink-0 items-center gap-0.5 text-xs font-semibold tabular-nums cursor-help',
            className,
          )}
        >
          <Icon className="size-3.5" />
          {headline}
        </span>
      </TooltipTrigger>
      <TooltipContent>
        {summary.total === 0 ? (
          <p>No issues reported</p>
        ) : (
          <div className="space-y-1">
            <p className="font-medium">
              {summary.total} reported {summary.total === 1 ? 'issue' : 'issues'}
            </p>
            <ul>
              {REPORTED_TIERS.filter((tier) => summary.counts[tier] > 0).map((tier) => {
                const { icon: TierIcon, label } = severityDisplay[tier];
                return (
                  <li key={tier} className="flex items-center gap-1.5">
                    <TierIcon className="size-3" />
                    <span className="tabular-nums">{summary.counts[tier]}</span> {label}
                  </li>
                );
              })}
            </ul>
            <p className="opacity-70">Passing checks and resolved issues are not counted.</p>
          </div>
        )}
      </TooltipContent>
    </Tooltip>
  );
}
