'use client';

import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { ChevronDownIcon, ChevronUpIcon } from 'lucide-react';

interface IssueNavProps {
  /** Where the reader stands in the walk, counting from one, or null before it. */
  position: number | null;
  total: number;
  onStep: (delta: 1 | -1) => void;
}

/**
 * Step to the next finding, or back to the one before it.
 *
 * Findings are not spread evenly through a document: it can carry nothing for
 * twenty pages and then eleven in a row. Without this the reader has to scroll
 * the whole quiet stretch to find that out, and in margin mode there is nothing
 * beside the text to tell them how much further to go.
 *
 * The count is here for the same reason — it answers how far through the review
 * they are, which neither the document nor the margin can say.
 *
 * Whether the width can carry this at all is the caller's to decide: stepping is
 * only worth offering while something on screen can show what it steps to.
 */
export function IssueNav({ position, total, onStep }: IssueNavProps) {
  if (total === 0) return null;

  return (
    <div className="flex items-center gap-0.5 rounded-md border p-0.5">
      <Step
        label="Previous issue"
        icon={ChevronUpIcon}
        // Nothing open means the reader has not started, so there is nothing
        // behind them; the first press has to go forwards.
        disabled={position === null || position <= 1}
        onClick={() => onStep(-1)}
      />
      <span className="px-1 font-mono text-[11px] tabular-nums text-muted-foreground">
        {position ?? '–'}/{total}
      </span>
      <Step
        label="Next issue"
        icon={ChevronDownIcon}
        disabled={position !== null && position >= total}
        onClick={() => onStep(1)}
      />
    </div>
  );
}

function Step({
  label,
  icon: Icon,
  disabled,
  onClick,
}: {
  label: string;
  icon: typeof ChevronUpIcon;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          onClick={onClick}
          disabled={disabled}
          aria-label={label}
          className={cn(
            'flex size-5 items-center justify-center rounded-sm text-muted-foreground transition-colors',
            disabled ? 'opacity-40' : 'hover:bg-accent/60 hover:text-foreground cursor-pointer',
          )}
        >
          <Icon className="size-3.5" />
        </button>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}
