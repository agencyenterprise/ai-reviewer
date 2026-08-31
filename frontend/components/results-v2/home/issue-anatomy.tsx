'use client';

import { SeverityEnum } from '@/lib/generated-api';
import { SEVERITY } from '@/lib/severity-style';
import { cn } from '@/lib/utils';
import { LightbulbIcon } from 'lucide-react';

/**
 * What an answer looks like when it comes back: a paragraph of the draft with a
 * note beside it, at the line the note is about.
 *
 * Built to the same proportions as the document explorer rather than described
 * in prose, because "issues appear in the margin" means nothing until you have
 * seen the margin. The text is invented; a real draft is the reader's own.
 */
export function IssueAnatomy() {
  return (
    <div className="overflow-hidden rounded-lg border bg-background shadow-sm">
      <div className="flex items-center gap-2 border-b px-3 py-2">
        <span className="font-mono text-[10px] tracking-wide text-muted-foreground uppercase">Document explorer</span>
        <span className="ml-auto font-mono text-[10px] tabular-nums text-muted-foreground">24 sections · 3 issues</span>
      </div>

      <div className="grid gap-x-4 p-4 sm:grid-cols-[minmax(0,1fr)_15rem]">
        <div className="min-w-0">
          <div className="flex gap-3">
            <span className="shrink-0 pt-0.5 font-mono text-[10px] leading-[1.7] tabular-nums text-muted-foreground/60">
              127
            </span>
            <p className="text-[13px] leading-relaxed">
              Grid-scale storage now covers{' '}
              <span
                className={cn(
                  'rounded-sm px-0.5 underline decoration-dotted underline-offset-2',
                  SEVERITY[SeverityEnum.High].wash,
                )}
              >
                40% of peak demand across three EU member states
              </span>{' '}
              <span className="text-muted-foreground">(Lindqvist, 2022)</span>, a share that has doubled since the
              previous review period.
            </p>
          </div>
        </div>

        <div className="mt-4 min-w-0 sm:mt-0">
          <div className={cn('rounded-md border', SEVERITY[SeverityEnum.High].edge, SEVERITY[SeverityEnum.High].wash)}>
            <div className="px-2.5 pt-2">
              <span className="flex items-center gap-1.5">
                <span className={cn('block size-1.5 shrink-0 rounded-full', SEVERITY[SeverityEnum.High].dot)} />
                <span className="truncate font-mono text-[10px] tracking-wide text-muted-foreground uppercase">
                  Claim Reference Validation
                </span>
                <span className="ml-auto font-mono text-[10px] tabular-nums text-muted-foreground">L127</span>
              </span>
              <p className="mt-0.5 text-[13px] leading-snug font-medium">Unsupported citation</p>
              <p className="mt-0.5 text-[12px] leading-snug text-muted-foreground">
                The cited review reports 22% across two member states, not 40% across three.
              </p>
            </div>

            <div className="px-2.5 pt-1.5 pb-2">
              <div className="rounded border border-dashed bg-background/60 px-2 py-1.5">
                <p className="mb-1 flex items-center gap-1 font-mono text-[9.5px] tracking-wide text-muted-foreground uppercase">
                  <LightbulbIcon className="size-3" aria-hidden />
                  Suggested action
                </p>
                <p className="text-[12px] leading-relaxed">
                  Quote the figure the source gives, or cite the later dataset the number came from.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
