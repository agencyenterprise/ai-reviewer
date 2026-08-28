'use client';

import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Issue } from '@/lib/generated-api';
import { getIssueCount, hasActiveFilters, useDocumentExplorerStore } from '@/lib/stores/document-explorer-store';
import { Loader2 } from 'lucide-react';
import { Ref, useImperativeHandle, useRef, useState } from 'react';
import { IssuesList, IssuesListHandle } from './issues-list';

export interface IssuesColumnHandle {
  scrollToIssue: (issue: Issue) => void;
}

interface IssuesColumnProps {
  ref?: Ref<IssuesColumnHandle>;
  /** Issues after the passing/resolved toggles, before severity and type. */
  visibleIssues: Issue[];
  /** Issues after every filter — what the list shows. */
  issues: Issue[];
  /** The issue whose row is expanded. */
  activeIssueId: string | null;
  isAnyProcessing: boolean;
  readOnly: boolean;
  onSelectIssue: (issue: Issue) => void;
}

/**
 * The whole issue queue, always. Selecting an issue or a paragraph opens and
 * scrolls to its row rather than narrowing the list to it: the margin already
 * answers "what is on this paragraph", so filtering here only cost the reader
 * their sense of what else the document holds.
 */
export function IssuesColumn({
  ref,
  visibleIssues,
  issues,
  activeIssueId,
  isAnyProcessing,
  readOnly,
  onSelectIssue,
}: IssuesColumnProps) {
  const { filter, clearFilters } = useDocumentExplorerStore();
  const [scrollContainer, setScrollContainer] = useState<HTMLDivElement | null>(null);
  const listRef = useRef<IssuesListHandle>(null);

  useImperativeHandle(ref, () => ({
    scrollToIssue: (issue: Issue) => {
      requestAnimationFrame(() => listRef.current?.scrollToIssue(issue));
    },
  }));

  const visibleCount = getIssueCount(visibleIssues);
  const shownCount = getIssueCount(issues);

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
            (shownCount === visibleCount ? `${visibleCount} issues` : `${shownCount} of ${visibleCount} issues`)}
          {visibleCount === 0 && isAnyProcessing && 'Finding issues...'}
          {visibleCount === 0 && !isAnyProcessing && 'No issues'}
        </span>
      </div>

      <div ref={setScrollContainer} className="min-h-0 flex-1 overflow-y-auto">
        {visibleIssues.length === 0 && !isAnyProcessing && (
          <p className="p-4 text-sm text-muted-foreground">No issues found for this document.</p>
        )}

        {visibleIssues.length > 0 && issues.length === 0 && !isAnyProcessing && (
          <div className="space-y-1 py-8 text-center text-sm text-muted-foreground">
            <p>No issues match the current filters.</p>
            {hasActiveFilters(filter) && (
              <Button variant="link" size="sm" className="text-xs" onClick={clearFilters}>
                Clear filters
              </Button>
            )}
          </div>
        )}

        <IssuesList
          ref={listRef}
          issues={issues}
          scrollElement={scrollContainer}
          activeIssueId={activeIssueId}
          onSelect={onSelectIssue}
          readOnly={readOnly}
        />
      </div>
    </div>
  );
}
