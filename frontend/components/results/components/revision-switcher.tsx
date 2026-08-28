'use client';

import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Check, ChevronDown, Plus } from 'lucide-react';

interface RevisionSwitcherProps {
  currentRevision: number;
  totalRevisions: number;
  selectedRevision: number;
  onRevisionChange: (revision: number) => void;
  /** Opens the dialog for uploading a new revision of the main document. */
  onCreateRevision?: () => void;
}

/**
 * Which revision of the main document is on screen.
 *
 * A menu rather than a select: it sits in a row of buttons, and a select's
 * trigger reads as a form field among them. It is also not really a form
 * field — one of its entries uploads a document rather than choosing a value.
 */
export function RevisionSwitcher({
  currentRevision,
  totalRevisions,
  selectedRevision,
  onRevisionChange,
  onCreateRevision,
}: RevisionSwitcherProps) {
  const revisions = Array.from({ length: totalRevisions }, (_, index) => totalRevisions - index);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        {/* The trigger names the revision only; which one is current is a
            distinction that matters while choosing, not while reading. */}
        <Button variant="outline" size="xs">
          Revision {selectedRevision}
          <ChevronDown className="text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end">
        {revisions.map((revision) => (
          <DropdownMenuItem key={revision} onSelect={() => onRevisionChange(revision)}>
            Revision {revision}
            {revision === currentRevision && <span className="text-muted-foreground">(current)</span>}
            {revision === selectedRevision && <Check className="ml-auto size-3.5" />}
          </DropdownMenuItem>
        ))}

        {onCreateRevision && (
          <>
            <DropdownMenuSeparator />
            <Tooltip>
              <TooltipTrigger asChild>
                <DropdownMenuItem onSelect={onCreateRevision}>
                  <Plus />
                  Create new revision...
                </DropdownMenuItem>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                A revision is a version of the main document. Creating one uploads a new version and makes it current;
                earlier revisions and their results are kept.
              </TooltipContent>
            </Tooltip>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
