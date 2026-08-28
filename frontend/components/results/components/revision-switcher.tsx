'use client';

import { Select, SelectContent, SelectItem, SelectSeparator, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { HelpCircle, Plus } from 'lucide-react';

// Sentinel value for the "Create new revision..." action so it can live inside
// the same Select without being mistaken for a revision number.
const CREATE_REVISION_VALUE = '__create_revision__';

interface RevisionSwitcherProps {
  currentRevision: number;
  totalRevisions: number;
  selectedRevision: number;
  onRevisionChange: (revision: number) => void;
  /** Opens the dialog for uploading a new revision of the main document. */
  onCreateRevision?: () => void;
}

export function RevisionSwitcher({
  currentRevision,
  totalRevisions,
  selectedRevision,
  onRevisionChange,
  onCreateRevision,
}: RevisionSwitcherProps) {
  const handleChange = (value: string) => {
    if (value === CREATE_REVISION_VALUE) {
      onCreateRevision?.();
      return;
    }
    onRevisionChange(Number(value));
  };

  return (
    <Select value={String(selectedRevision)} onValueChange={handleChange}>
      <SelectTrigger className="h-7 w-auto gap-1 text-xs">
        {/* The trigger names the revision only; which one is current is a
            distinction that matters while choosing, not while reading. */}
        <SelectValue>Revision {selectedRevision}</SelectValue>
      </SelectTrigger>
      <SelectContent>
        {Array.from({ length: totalRevisions }, (_, i) => totalRevisions - i).map((rev) => (
          <SelectItem key={rev} value={String(rev)}>
            Revision {rev}
            {rev === currentRevision ? ' (current)' : ''}
          </SelectItem>
        ))}
        {onCreateRevision && (
          <>
            <SelectSeparator />
            <SelectItem value={CREATE_REVISION_VALUE}>
              <span className="flex items-center gap-1.5 text-muted-foreground text-xs">
                <Plus className="size-3.5" />
                Create new revision...
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span
                      className="inline-flex"
                      onPointerDown={(e) => e.stopPropagation()}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <HelpCircle className="size-3.5" />
                    </span>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    A revision is a version of the main document. Creating one uploads a new version and makes it
                    current; earlier revisions and their results are kept.
                  </TooltipContent>
                </Tooltip>
              </span>
            </SelectItem>
          </>
        )}
      </SelectContent>
    </Select>
  );
}
