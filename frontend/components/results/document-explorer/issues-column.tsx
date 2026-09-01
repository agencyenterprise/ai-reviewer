'use client';

import { Button } from '@/components/ui/button';
import { Issue } from '@/lib/generated-api';
import { getIssueCount, hasActiveFilters, useDocumentExplorerStore } from '@/lib/stores/document-explorer-store';
import { CheckCircle2, FileSearch, Loader2 } from 'lucide-react';
import { ReactNode, Ref, useImperativeHandle, useRef, useState } from 'react';
import { NewAssessmentButton } from '../new-assessment-button';
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
  projectId: string;
  /** Issues after the passing/resolved toggles, before severity and type. */
  visibleIssues: Issue[];
  /** Issues after every filter — what the list shows. */
  issues: Issue[];
  /** Every issue on the document, before any filtering. */
  totalIssueCount: number;
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
  projectId,
  visibleIssues,
  issues,
  totalIssueCount,
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
        {visibleIssues.length === 0 && (
          <EmptyIssues
            projectId={projectId}
            totalIssueCount={totalIssueCount}
            isAnyProcessing={isAnyProcessing}
            readOnly={readOnly}
          />
        )}

        {visibleIssues.length > 0 && issues.length === 0 && (
          <EmptyState title="No issues match the current filters">
            {hasActiveFilters(filter) && (
              <Button variant="link" size="sm" className="text-xs" onClick={clearFilters}>
                Clear filters
              </Button>
            )}
          </EmptyState>
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

/**
 * What the column says when it has nothing to list. Never nothing: an empty
 * panel reads as something that failed to load, and the three ways to arrive
 * here want different answers — wait, clear a toggle, or run an assessment.
 */
function EmptyIssues({
  projectId,
  totalIssueCount,
  isAnyProcessing,
  readOnly,
}: {
  projectId: string;
  totalIssueCount: number;
  isAnyProcessing: boolean;
  readOnly: boolean;
}) {
  const { setFilter } = useDocumentExplorerStore();

  if (isAnyProcessing) {
    return (
      <EmptyState
        icon={<Loader2 className="size-5 animate-spin" />}
        title="No issues yet"
        description="Assessments are still running. Findings appear here as they land."
      />
    );
  }

  // Issues exist, but every one of them is resolved or passing and the toggles
  // that would show them are off. Saying "no issues" here would be a lie about
  // the document rather than about the filters.
  if (totalIssueCount > 0) {
    return (
      <EmptyState
        icon={<CheckCircle2 className="size-5" />}
        title="No open issues"
        description="Every issue on this document is resolved or passing."
      >
        <Button
          variant="link"
          size="sm"
          className="text-xs"
          onClick={() => setFilter({ showResolved: true, showPassing: true })}
        >
          Show resolved and passing
        </Button>
      </EmptyState>
    );
  }

  return (
    <EmptyState
      icon={<FileSearch className="size-5" />}
      title="No issues found"
      description={
        readOnly
          ? 'No assessment has reported anything on this document.'
          : 'Run an assessment to have this document reviewed.'
      }
    >
      {!readOnly && <NewAssessmentButton projectId={projectId} collapseLabel={false} />}
    </EmptyState>
  );
}

function EmptyState({
  icon,
  title,
  description,
  children,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-2 px-6 py-10 text-center text-sm text-muted-foreground">
      {icon && <span className="text-muted-foreground/70">{icon}</span>}
      <p className="font-medium text-foreground">{title}</p>
      {description && <p className="text-xs text-balance">{description}</p>}
      {children}
    </div>
  );
}
