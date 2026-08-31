import { cn } from '@/lib/utils';
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';
import { computeDelta, formatCompact } from './format';

interface StatTileProps {
  label: string;
  value: number;
  /** Same metric over the preceding window; omitted when there is nothing to compare. */
  previous?: number;
  /** Name of the comparison period, e.g. "previous 30 days". */
  comparisonLabel?: string;
  hint?: string;
}

/**
 * Label · value · delta. Every metric here is one where up is good, so the
 * arrow direction and the colour agree; the arrow carries the direction so it
 * never rests on colour alone.
 */
export function StatTile({ label, value, previous, comparisonLabel, hint }: StatTileProps) {
  const delta = previous === undefined ? null : computeDelta(value, previous);
  const Icon =
    delta === null
      ? Minus
      : delta.direction === 'up'
        ? ArrowUpRight
        : delta.direction === 'down'
          ? ArrowDownRight
          : Minus;

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 text-3xl font-semibold text-foreground">{formatCompact(value)}</p>
      {delta && (
        <p className="mt-1.5 flex items-center gap-1 text-xs">
          <Icon
            className={cn(
              'h-3.5 w-3.5',
              delta.direction === 'up' && 'text-[var(--viz-good)]',
              delta.direction === 'down' && 'text-[var(--viz-critical)]',
              delta.direction === 'flat' && 'text-muted-foreground',
            )}
            aria-hidden
          />
          <span className="font-medium text-foreground">{delta.label}</span>
          <span className="text-muted-foreground">vs {comparisonLabel ?? 'previous period'}</span>
        </p>
      )}
      {hint && <p className="mt-1.5 text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}
