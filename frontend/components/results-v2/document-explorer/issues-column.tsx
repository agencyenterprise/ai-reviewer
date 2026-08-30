'use client';

import { Button } from '@/components/ui/button';
import { Issue } from '@/lib/generated-api';
import { getIssueCount, hasActiveFilters, useDocumentExplorerStore } from '@/lib/stores/document-explorer-store';
import { Ref, useImperativeHandle, useRef, useState } from 'react';
import { IssuesList, IssuesListHandle } from './issues-list';

/**
 * "12 issues", or "3 of 12 issues" once filters narrow the list. Null when the
 * document has none to report, so callers can leave the slot empty.
 */
export function issueCountLabel(visibleIssues: Issue[], issues: Issue[]): string | null {
  const visibleCount = getIssueCount(visibleIssues);
  if (visibleCount === 0) return null;

  const shownCount = getIssueCount(issues);
  const noun = visibleCount === 1 ? 'issue' : 'issues';
  return shownCount === visibleCount ? `${visibleCount} ${noun}` : `${shownCount} of ${visibleCount} ${noun}`;
}

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

  return (
    <div className="flex h-full flex-col">
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
