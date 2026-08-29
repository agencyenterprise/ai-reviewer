'use client';

import { Button } from '@/components/ui/button';
import { History } from 'lucide-react';

interface OldRevisionBannerProps {
  selectedRevision: number;
  currentRevision: number;
  onViewCurrent?: () => void;
}

/**
 * The strip that appears while an earlier revision is on screen. It sits in the
 * chrome rather than at the top of the document, because everything below it
 * belongs to that revision — its issues, its files, its results — and the
 * notice would otherwise scroll away and take the explanation with it.
 */
export function OldRevisionBanner({ selectedRevision, currentRevision, onViewCurrent }: OldRevisionBannerProps) {
  return (
    <div className="flex shrink-0 flex-wrap items-center gap-3 border-b bg-blue-50 px-3 py-2 dark:bg-blue-950/30">
      <History className="size-4 shrink-0 text-blue-700 dark:text-blue-400" />
      <p className="min-w-0 text-sm">
        <strong className="font-medium">Viewing revision {selectedRevision}.</strong>{' '}
        <span className="text-muted-foreground">
          This is an earlier draft, kept as it was, so nothing here can be changed.
        </span>
      </p>

      {onViewCurrent && (
        <div className="ml-auto flex shrink-0 items-center gap-2">
          <Button size="xs" variant="outline" className="h-6" onClick={onViewCurrent}>
            View revision {currentRevision}
          </Button>
        </div>
      )}
    </div>
  );
}
