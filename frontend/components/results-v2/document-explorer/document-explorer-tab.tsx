'use client';

import { Button } from '@/components/ui/button';
import { Callout } from '@/components/ui/callout';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Issue, ProjectDetailed, WorkflowRunType } from '@/lib/generated-api';
import { useLineHashNavigation } from '@/lib/line-hash';
import {
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
import { WIDE_ENOUGH_FOR_PANE, useMediaQuery } from '@/lib/use-media-query';
import { cn } from '@/lib/utils';
import { AlertTriangleIcon, Columns2, ListFilter, Loader2 } from 'lucide-react';
import { useCallback, useMemo, useRef, useState } from 'react';
import { DocumentHeader, DocumentView, DocumentViewHandle } from './document-view';
import { IssuesColumn, IssuesColumnHandle, issueCountLabel } from './issues-column';
import { Rail, RailToggle, SidePane, useRailState } from '../panes';
import { OutlineRail } from './outline-rail';
import { OutlineEntry, extractOutline } from './outline';

/** The two ways to read the issues: beside the text, or gathered in a column. */
const MODES = [
  {
    id: 'margin' as const,
    label: 'Margin',
    icon: Columns2,
    hint: 'Issues sit beside the paragraph they belong to',
  },
  { id: 'list' as const, label: 'List', icon: ListFilter, hint: 'Issues in one column, grouped by severity' },
];

interface DocumentExplorerTabProps {
  projectDetail: ProjectDetailed;
  readOnly?: boolean;
  onNavigateToAnalyses: () => void;
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
}: DocumentExplorerTabProps) {
  const { selectedLineRange, selectLineRange, clearLineSelection, filter, setFilter, clearFilters } =
    useDocumentExplorerStore();

  const rail = useRailState();
  const isWideEnoughForColumn = useMediaQuery(WIDE_ENOUGH_FOR_PANE);
  const [issuesOpen, setIssuesOpen] = useState(false);
  const [activeLine, setActiveLine] = useState<number | null>(null);
  // Margin puts each issue beside its paragraph in one shared scroll; list keeps
  // the ranked queue in a column of its own.
  const [mode, setMode] = useState<'margin' | 'list'>('margin');
  // Which margin note is open. Tracked rather than derived from the line range,
  // because several issues can share a range and the one you clicked is the one
  // that should expand.
  const [openIssueId, setOpenIssueId] = useState<string | null>(null);

  const mainDocumentMarkdown = projectDetail.main_document_markdown ?? '';

  const workflowDetails = useMemo(() => projectDetail.workflow_runs ?? [], [projectDetail.workflow_runs]);
  const issues = useMemo(() => projectDetail.issues ?? [], [projectDetail.issues]);

  const documentSummarization = getWorkflowRunByType(workflowDetails, WorkflowRunType.DocumentSummarization);
  // What the summarizer read off the document itself, which is what the reader
  // wants at the top of the page — not the project's name, which is editable
  // and often just the uploaded file name.
  const documentHeader = useMemo<DocumentHeader | undefined>(() => {
    const state = documentSummarization?.state;
    const summary = state?.summaries?.find((item) => item.file_id === state.main_file_id);
    if (!summary) return undefined;
    return { title: summary.title, authors: summary.authors };
  }, [documentSummarization]);

  const documentProcessing = getWorkflowRunByType(workflowDetails, WorkflowRunType.DocumentProcessing);
  const isDocumentProcessing = isWorkflowProcessing(documentProcessing);
  const isAnyProcessing = isAnyWorkflowProcessing(workflowDetails);

  const issuesRef = useRef<IssuesColumnHandle>(null);
  const documentRef = useRef<DocumentViewHandle>(null);

  const workflowErrors = useMemo(() => getBlockingWorkflowErrors(workflowDetails), [workflowDetails]);
  const outline = useMemo(() => extractOutline(mainDocumentMarkdown), [mainDocumentMarkdown]);
  const visibleIssues = useMemo(() => getVisibleIssues(issues, filter), [issues, filter]);
  const resolvedCount = useMemo(() => getResolvedCount(issues, null), [issues]);
  const passingCount = useMemo(() => getPassingCount(issues), [issues]);
  const highlightIssues = useMemo(() => getHighlightIssues(visibleIssues, filter), [visibleIssues, filter]);

  // Falls back to the first issue on the selected lines, so arriving on a #L… hash
  // from another tab still opens something.
  const activeIssueId = useMemo(() => {
    // Before the range check: an issue the reader opened stays open even when it
    // has no lines to select, which is the only way to read one that carries
    // none — nothing anchors it in the document for the fallback below to find.
    if (openIssueId && highlightIssues.some((issue) => issue.id === openIssueId)) return openIssueId;
    if (!selectedLineRange) return null;
    const match = highlightIssues.find((issue) => {
      const range = getIssueLineRange(issue);
      return range !== null && range[0] <= selectedLineRange[1] && range[1] >= selectedLineRange[0];
    });
    return match?.id ?? null;
  }, [highlightIssues, selectedLineRange, openIssueId]);

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

  const showIssuesColumn = isWideEnoughForColumn && (mode === 'list' || !rail.isWide);
  // Margin notes only render once the document has a margin to put them in,
  // which is the same width the rail sits beside the text at.
  const issuesVisible = showIssuesColumn || (mode === 'margin' && rail.isWide);

  const handleSelectIssue = useCallback(
    (issue: Issue) => {
      // Pressing the open row's heading closes it, as pressing the open note's
      // does in the margin: the two are the same control on the same issue, so
      // they cannot answer the same press differently.
      if (openIssueId === issue.id) {
        setOpenIssueId(null);
        clearLineSelection();
        return;
      }

      const range = getIssueLineRange(issue);
      // Opening the issue does not depend on it having a range: start_line is
      // nullable, and an issue with none can only be read here.
      setOpenIssueId(issue.id);
      issuesRef.current?.scrollToIssue(issue);
      if (range) {
        selectLineRange(range);
        documentRef.current?.scrollToLineRange(range);
      } else {
        clearLineSelection();
      }
    },
    [openIssueId, selectLineRange, clearLineSelection],
  );

  /** Toggles a margin note without moving the document under the reader. */
  const handleToggleMarginNote = useCallback(
    (issue: Issue) => {
      if (openIssueId === issue.id) {
        setOpenIssueId(null);
        clearLineSelection();
        return;
      }
      const range = getIssueLineRange(issue);
      setOpenIssueId(issue.id);
      if (range) selectLineRange(range);
      else clearLineSelection();
    },
    [openIssueId, selectLineRange, clearLineSelection],
  );

  const handleIssueSelectFromDocument = useCallback(
    (issue: Issue | null) => {
      if (!issue) {
        setOpenIssueId(null);
        clearLineSelection();
        return;
      }
      const range = getIssueLineRange(issue);
      if (!range) return;

      setOpenIssueId(issue.id);
      selectLineRange(range);

      if (issuesVisible) {
        issuesRef.current?.scrollToIssue(issue);
        return;
      }

      // Nowhere on screen is showing this issue, so bring the pane out and
      // scroll once it has mounted — the ref is null until the sheet opens.
      setIssuesOpen(true);
      setTimeout(() => issuesRef.current?.scrollToIssue(issue), 250);
    },
    [issuesVisible, selectLineRange, clearLineSelection],
  );

  /**
   * Margin rows grow to fit the notes beside them, so the document is taller in
   * margin mode than in list mode. Switching therefore lands on a different part
   * of the text unless the reader's place is carried across.
   */
  const handleModeChange = useCallback(
    (next: 'margin' | 'list') => {
      if (next === mode) return;
      const line = documentRef.current?.getTopVisibleLine() ?? null;
      setMode(next);
      if (line !== null) {
        setTimeout(() => documentRef.current?.scrollToLine(line, 'auto'), 0);
      }
    },
    [mode],
  );

  // Margin mode puts the issues beside the text, so the column only earns its
  // place there while the margin itself is too narrow to appear.

  const countLabel = issueCountLabel(visibleIssues, highlightIssues);

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
        <Rail state={rail} label="Filters and outline">
          <OutlineRail
            outline={outline}
            visibleIssues={visibleIssues}
            markedIssues={highlightIssues}
            filter={filter}
            onFilterChange={setFilter}
            onClearFilters={clearFilters}
            resolvedCount={resolvedCount}
            passingCount={passingCount}
            activeLine={activeLine}
            onJump={(entry) => {
              handleJumpToSection(entry);
              rail.close();
            }}
          />
        </Rail>

        <main className="flex min-w-0 flex-1 flex-col">
          <div className="flex h-10 shrink-0 items-center gap-2 border-b px-2">
            <RailToggle state={rail} label="Filters and outline" />
            <span className="truncate text-xs text-muted-foreground">
              {outline.length > 0 ? `${outline.length} sections` : 'Document'}
              {mainDocumentMarkdown ? ` · ${mainDocumentMarkdown.split('\n').length} lines` : ''}
              {` · ${countLabel ?? (isAnyProcessing ? 'Finding issues...' : 'No issues')}`}
            </span>

            {isAnyProcessing && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <span
                    className="inline-flex size-3.5 shrink-0 items-center justify-center text-muted-foreground"
                    aria-label="Some results are still loading"
                  >
                    <Loader2 className="size-3.5 animate-spin" />
                  </span>
                </TooltipTrigger>
                <TooltipContent>Some results are still loading, see the Assessments tab for details</TooltipContent>
              </Tooltip>
            )}

            {!issuesVisible && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button size="xs" variant="outline" className="ml-auto" onClick={() => setIssuesOpen(true)}>
                    <ListFilter className="size-3" />
                    Issues
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Every issue found in this document</TooltipContent>
              </Tooltip>
            )}

            <div className="ml-auto hidden items-center gap-1 rounded-md border p-0.5 xl:flex">
              {MODES.map((option) => (
                <Tooltip key={option.id}>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => handleModeChange(option.id)}
                      aria-pressed={mode === option.id}
                      className={cn(
                        'flex cursor-pointer items-center gap-1.5 rounded-sm px-2 py-0.5 text-xs font-medium transition-colors',
                        mode === option.id
                          ? 'bg-accent text-accent-foreground'
                          : 'text-muted-foreground hover:bg-accent/60',
                      )}
                    >
                      <option.icon className="size-3.5" />
                      {option.label}
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>{option.hint}</TooltipContent>
                </Tooltip>
              ))}
            </div>
          </div>

          <div className="min-h-0 flex-1">
            <DocumentView
              ref={documentRef}
              markdown={mainDocumentMarkdown}
              header={documentHeader}
              issues={highlightIssues}
              selectedLineRange={selectedLineRange}
              onIssueSelect={handleIssueSelectFromDocument}
              margin={mode === 'margin' ? { activeIssueId, readOnly, onSelect: handleToggleMarginNote } : undefined}
            />
          </div>
        </main>

        {/* A column wherever the margin is not already carrying the issues,
            and a sheet the reader opens below that width — where neither the
            margin nor a column fits. */}
        {/* Asking for the pane must not keep it around once the margin or the
            column has taken the issues back. */}
        <SidePane
          open={showIssuesColumn || (!issuesVisible && issuesOpen)}
          onClose={() => setIssuesOpen(false)}
          label="Issues"
        >
          <IssuesColumn
            ref={issuesRef}
            visibleIssues={visibleIssues}
            issues={highlightIssues}
            activeIssueId={activeIssueId}
            isAnyProcessing={isAnyProcessing}
            readOnly={readOnly}
            onSelectIssue={handleSelectIssue}
          />
        </SidePane>
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
