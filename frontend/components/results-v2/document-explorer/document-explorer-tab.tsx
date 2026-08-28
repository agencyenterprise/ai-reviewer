'use client';

import { Button } from '@/components/ui/button';
import { Callout } from '@/components/ui/callout';
import { Issue, ProjectDetailed, WorkflowRunType } from '@/lib/generated-api';
import { useLineHashNavigation } from '@/lib/line-hash';
import {
  getFilteredIssues,
  getHighlightIssues,
  getPassingCount,
  getResolvedCount,
  getVisibleIssues,
  LineRange,
  useDocumentExplorerStore,
} from '@/lib/stores/document-explorer-store';
import {
  getBlockingWorkflowErrors,
  getWorkflowRunByType,
  isAnyWorkflowProcessing,
  isWorkflowProcessing,
} from '@/lib/workflow-state';
import { cn } from '@/lib/utils';
import { AlertTriangleIcon, History, Loader2, PanelLeft } from 'lucide-react';
import { useCallback, useMemo, useRef, useState } from 'react';
import { DocumentView, DocumentViewHandle } from './document-view';
import { IssuesColumn, IssuesColumnHandle } from './issues-column';
import { OutlineRail } from './outline-rail';
import { OutlineEntry, extractOutline } from './outline';

interface DocumentExplorerTabProps {
  projectDetail: ProjectDetailed;
  readOnly?: boolean;
  onNavigateToAnalyses: () => void;
  /** Currently displayed revision (for the non-current revision notice). */
  selectedRevision?: number;
  /** Callback to switch revisions (used by the "View current revision" action). */
  onRevisionChange?: (revision: number) => void;
}

type IssueWithLines = Issue & { start_line?: number | null; end_line?: number | null };

function getIssueLineRange(issue: Issue): [number, number] | null {
  const { start_line, end_line } = issue as IssueWithLines;
  if (typeof start_line !== 'number' || typeof end_line !== 'number') return null;
  return [start_line, end_line];
}

export function DocumentExplorerTabV2({
  projectDetail,
  readOnly = false,
  onNavigateToAnalyses,
  selectedRevision,
  onRevisionChange,
}: DocumentExplorerTabProps) {
  const { selectedLineRange, selectLineRange, clearLineSelection, filter, setFilter, clearFilters } =
    useDocumentExplorerStore();

  const [railOpen, setRailOpen] = useState(true);
  const [activeLine, setActiveLine] = useState<number | null>(null);

  const mainDocumentMarkdown = projectDetail.main_document_markdown ?? '';
  const currentRevision = projectDetail.project.current_revision ?? 1;
  const isViewingOlderRevision = selectedRevision != null && selectedRevision !== currentRevision;

  const workflowDetails = useMemo(() => projectDetail.workflow_runs ?? [], [projectDetail.workflow_runs]);
  const issues = useMemo(() => projectDetail.issues ?? [], [projectDetail.issues]);

  const documentProcessing = getWorkflowRunByType(workflowDetails, WorkflowRunType.DocumentProcessing);
  const isDocumentProcessing = isWorkflowProcessing(documentProcessing);
  const isAnyProcessing = isAnyWorkflowProcessing(workflowDetails);

  const issuesRef = useRef<IssuesColumnHandle>(null);
  const documentRef = useRef<DocumentViewHandle>(null);

  const workflowErrors = useMemo(() => getBlockingWorkflowErrors(workflowDetails), [workflowDetails]);
  const outline = useMemo(() => extractOutline(mainDocumentMarkdown), [mainDocumentMarkdown]);
  const visibleIssues = useMemo(() => getVisibleIssues(issues, filter), [issues, filter]);
  const resolvedCount = useMemo(() => getResolvedCount(issues, selectedLineRange), [issues, selectedLineRange]);
  const passingCount = useMemo(() => getPassingCount(issues), [issues]);
  const filteredIssues = useMemo(
    () => getFilteredIssues(visibleIssues, filter, selectedLineRange),
    [visibleIssues, filter, selectedLineRange],
  );
  const highlightIssues = useMemo(() => getHighlightIssues(visibleIssues, filter), [visibleIssues, filter]);

  // Landing on a #L… hash (e.g. from an issue in another tab) both filters to
  // that range and brings it into view, matching a click on an issue in-tab.
  const handleLineHashNavigation = useCallback(
    (range: LineRange) => {
      selectLineRange(range);
      documentRef.current?.scrollToLineRange(range);
    },
    [selectLineRange],
  );

  useLineHashNavigation(handleLineHashNavigation);

  const handleSelectIssue = useCallback(
    (issue: Issue) => {
      const range = getIssueLineRange(issue);
      if (range) {
        selectLineRange(range);
        issuesRef.current?.scrollToIssue(issue);
        documentRef.current?.scrollToLineRange(range);
      } else {
        clearLineSelection();
      }
    },
    [selectLineRange, clearLineSelection],
  );

  const handleIssueSelectFromDocument = useCallback(
    (issue: Issue | null) => {
      if (!issue) {
        clearLineSelection();
        return;
      }
      const range = getIssueLineRange(issue);
      if (range) {
        selectLineRange(range);
        issuesRef.current?.scrollToIssue(issue);
      }
    },
    [selectLineRange, clearLineSelection],
  );

  const handleJumpToSection = useCallback((entry: OutlineEntry) => {
    setActiveLine(entry.line);
    documentRef.current?.scrollToLine(entry.line);
  }, []);

  if (isDocumentProcessing && !mainDocumentMarkdown) {
    return (
      <div className="space-y-4 p-6">
        {workflowErrors.length > 0 && <ProcessingErrorNotice onNavigateToAnalyses={onNavigateToAnalyses} />}
        <div className="flex items-center justify-center py-12">
          <div className="space-y-3 text-center">
            <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Processing document(s)...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-lg">
      {workflowErrors.length > 0 && (
        <div className="border-b p-3">
          <ProcessingErrorNotice onNavigateToAnalyses={onNavigateToAnalyses} />
        </div>
      )}

      <div className="flex min-h-0 flex-1">
        <aside
          className={cn(
            'bg-sidebar hidden shrink-0 border-r transition-[width] xl:block',
            railOpen ? 'w-72' : 'w-0 overflow-hidden border-r-0',
          )}
        >
          <OutlineRail
            outline={outline}
            visibleIssues={visibleIssues}
            filter={filter}
            onFilterChange={setFilter}
            onClearFilters={clearFilters}
            resolvedCount={resolvedCount}
            passingCount={passingCount}
            activeLine={activeLine}
            onJump={handleJumpToSection}
          />
        </aside>

        <main className="flex min-w-0 flex-1 flex-col">
          <div className="flex h-10 shrink-0 items-center gap-2 border-b px-2">
            <Button
              variant="ghost"
              size="icon"
              className="hidden size-7 xl:flex"
              onClick={() => setRailOpen(!railOpen)}
              aria-label={railOpen ? 'Hide contents' : 'Show contents'}
              aria-pressed={railOpen}
            >
              <PanelLeft className="size-4" />
            </Button>
            <span className="truncate text-xs text-muted-foreground">
              {outline.length > 0 ? `${outline.length} sections` : 'Document'}
              {mainDocumentMarkdown ? ` · ${mainDocumentMarkdown.split('\n').length} lines` : ''}
            </span>
          </div>

          <div className="min-h-0 flex-1">
            <DocumentView
              ref={documentRef}
              markdown={mainDocumentMarkdown}
              issues={highlightIssues}
              selectedLineRange={selectedLineRange}
              onIssueSelect={handleIssueSelectFromDocument}
              header={
                isViewingOlderRevision ? (
                  <Callout variant="info" icon={History} title={`Viewing revision ${selectedRevision}`}>
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <p className="min-w-0 text-sm">
                        You are viewing a previous revision of the main document (revision {selectedRevision}).
                      </p>
                      {onRevisionChange && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="shrink-0"
                          onClick={() => onRevisionChange(currentRevision)}
                        >
                          View current
                        </Button>
                      )}
                    </div>
                  </Callout>
                ) : undefined
              }
            />
          </div>
        </main>

        <aside className="hidden w-[24rem] shrink-0 border-l lg:block xl:w-[26rem]">
          <IssuesColumn
            ref={issuesRef}
            visibleIssues={visibleIssues}
            filteredIssues={filteredIssues}
            isAnyProcessing={isAnyProcessing}
            readOnly={readOnly}
            onSelectIssue={handleSelectIssue}
            onClearSelection={clearLineSelection}
          />
        </aside>
      </div>
    </div>
  );
}

function ProcessingErrorNotice({ onNavigateToAnalyses }: { onNavigateToAnalyses: () => void }) {
  return (
    <Callout variant="warning" icon={AlertTriangleIcon} title="Unexpected processing errors occurred">
      <p className="text-sm">
        Check the{' '}
        <button onClick={onNavigateToAnalyses} className="cursor-pointer font-medium underline underline-offset-2">
          Assessments tab
        </button>{' '}
        for details.
      </p>
    </Callout>
  );
}
