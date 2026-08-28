'use client';

import { DocumentIssuesList, DocumentIssuesListHandle } from '@/components/results/components/document-issues-list';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Issue } from '@/lib/generated-api';
import { getIssueCount, hasActiveFilters, useDocumentExplorerStore } from '@/lib/stores/document-explorer-store';
import { Loader2, X } from 'lucide-react';
import { Ref, useImperativeHandle, useRef, useState } from 'react';

export interface IssuesColumnHandle {
  scrollToIssue: (issue: Issue) => void;
}

interface IssuesColumnProps {
  ref?: Ref<IssuesColumnHandle>;
  visibleIssues: Issue[];
  filteredIssues: Issue[];
  isAnyProcessing: boolean;
  readOnly: boolean;
  onSelectIssue: (issue: Issue) => void;
  onClearSelection: () => void;
}

export function IssuesColumn({
  ref,
  visibleIssues,
  filteredIssues,
  isAnyProcessing,
  readOnly,
  onSelectIssue,
  onClearSelection,
}: IssuesColumnProps) {
  const { selectedLineRange, filter, clearFilters } = useDocumentExplorerStore();
  const [scrollContainer, setScrollContainer] = useState<HTMLDivElement | null>(null);
  const listRef = useRef<DocumentIssuesListHandle>(null);

  useImperativeHandle(ref, () => ({
    scrollToIssue: (issue: Issue) => {
      requestAnimationFrame(() => listRef.current?.scrollToIssue(issue));
    },
  }));

  const visibleCount = getIssueCount(visibleIssues);
  const filteredCount = getIssueCount(filteredIssues);

  const selectionLabel = selectedLineRange
    ? selectedLineRange[0] === selectedLineRange[1]
      ? `Line ${selectedLineRange[0]}`
      : `Lines ${selectedLineRange[0]}–${selectedLineRange[1]}`
    : null;

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-10 shrink-0 items-center gap-2 border-b px-4">
        <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
          {isAnyProcessing && (
            <Tooltip>
              <TooltipTrigger asChild>
                <span
                  className="inline-flex size-3.5 items-center justify-center"
                  aria-label="Some results are still loading"
                >
                  <Loader2 className="size-3.5 animate-spin" />
                </span>
              </TooltipTrigger>
              <TooltipContent>Some results are still loading, see the Assessments tab for details</TooltipContent>
            </Tooltip>
          )}
          {visibleCount > 0 &&
            (filteredCount === visibleCount ? `${visibleCount} issues` : `${filteredCount} of ${visibleCount} issues`)}
          {visibleCount === 0 && isAnyProcessing && 'Finding issues...'}
          {visibleCount === 0 && !isAnyProcessing && 'No issues'}
        </span>

        {selectionLabel && (
          <Button variant="outline" size="sm" className="ml-auto h-6 gap-1 px-2 text-xs" onClick={onClearSelection}>
            {selectionLabel}
            <X />
          </Button>
        )}
      </div>

      <div ref={setScrollContainer} className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
        {visibleIssues.length === 0 && !isAnyProcessing && (
          <p className="py-4 text-sm text-muted-foreground">No issues found for this document.</p>
        )}

        {visibleIssues.length > 0 && filteredIssues.length === 0 && !isAnyProcessing && (
          <div className="space-y-1 py-8 text-center text-sm text-muted-foreground">
            <p>{selectedLineRange ? 'No issues on the selected lines.' : 'No issues match the current filters.'}</p>
            {hasActiveFilters(filter) && !selectedLineRange && (
              <Button variant="link" size="sm" className="text-xs" onClick={clearFilters}>
                Clear filters
              </Button>
            )}
          </div>
        )}

        <DocumentIssuesList
          ref={listRef}
          issues={filteredIssues}
          scrollElement={scrollContainer}
          hideJumpButton={selectedLineRange !== null}
          onSelect={onSelectIssue}
          readOnly={readOnly}
        />
      </div>
    </div>
  );
}
