'use client';

import { AnalysisOptionsMenu } from '@/components/results/components/analysis-options-menu';
import { TabType } from '@/components/results/constants';
import { ProjectViewProvider } from '@/components/results/project-view-context';
import {
  derivePeerReviewFacts,
  peerReviewNeedsAttention,
} from '@/components/results/tabs/peer-review/peer-review-derive';
import { UnmatchedReferencesApproveDialog } from '@/components/results/tabs/reference-review/unmatched-references-approve-dialog';
import { useReferenceApprovalFlow } from '@/components/results/tabs/reference-review/use-reference-approval-flow';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { EditableTitle } from '@/components/ui/editable-title';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ProjectFeedbackProvider } from '@/lib/contexts/project-feedback-context';
import { ProjectDetailed, WorkflowRunType } from '@/lib/generated-api';
import { useWorkflowTypes } from '@/lib/hooks/use-workflow-types';
import { getWorkflowRunByType } from '@/lib/workflow-state';
import { BookOpen, Loader2 } from 'lucide-react';
import { ReactNode, useMemo } from 'react';
import { AppBar } from './app-bar';

interface ProjectShellV2Props {
  projectDetail: ProjectDetailed;
  activeTab: TabType;
  onTabChange: (tab: TabType, hash?: string) => void;
  readOnly?: boolean;
  onTitleSave?: (newTitle: string) => Promise<void>;
  isTitleSaving?: boolean;
  needsReferenceReview?: boolean;
  selectedRevision?: number;
  onRevisionChange?: (revision: number) => void;
  onRevisionCreated?: () => void;
  children: ReactNode;
}

/**
 * Workbench chrome: one row for the application, one for the project, and the
 * rest of the viewport for the tab. Replaces both ApplicationShell's nav and the
 * stacked title block, which together cost about 160px before any content.
 *
 * The authors line is deliberately gone — it is in the document itself.
 */
export function ProjectShellV2({
  projectDetail,
  activeTab,
  onTabChange,
  readOnly = false,
  onTitleSave,
  isTitleSaving = false,
  needsReferenceReview = false,
  selectedRevision,
  onRevisionChange,
  onRevisionCreated,
  children,
}: ProjectShellV2Props) {
  const results = useMemo(() => projectDetail.workflow_runs ?? [], [projectDetail.workflow_runs]);
  const { isWorkflowTypeVisible } = useWorkflowTypes();

  const referenceExtraction = getWorkflowRunByType(results, WorkflowRunType.ReferenceExtraction);
  const referenceApproval = useReferenceApprovalFlow(projectDetail, projectDetail.project.id);

  const peerReviewFacts = derivePeerReviewFacts(projectDetail);
  const peerReviewAttention = peerReviewNeedsAttention(peerReviewFacts, readOnly);

  const navigateToTab = (tab: TabType, hash?: string) => onTabChange(tab, hash);

  return (
    <ProjectFeedbackProvider
      projectId={readOnly ? undefined : projectDetail.project.id}
      feedbackVisibility={readOnly ? null : (projectDetail.project.feedback_visibility ?? null)}
    >
      <ProjectViewProvider
        value={{
          projectDetail,
          readOnly,
          selectedRevision,
          onRevisionChange,
          onRevisionCreated,
          navigateToTab,
        }}
      >
        <div className="bg-background text-foreground flex h-dvh flex-col">
          <AppBar />

          {/* This project: what you are looking at, and the ways into it. */}
          <header className="flex h-12 shrink-0 items-center gap-3 border-b px-3">
            <div className="flex min-w-0 max-w-md flex-1 items-center">
              {!readOnly && onTitleSave ? (
                <EditableTitle
                  title={projectDetail.project.title}
                  titleClassName="text-sm font-semibold truncate"
                  className="min-w-0"
                  onSave={onTitleSave}
                  isLoading={isTitleSaving}
                />
              ) : (
                <h1 className="truncate text-sm font-semibold">{projectDetail.project.title}</h1>
              )}
            </div>

            <Tabs
              value={activeTab}
              onValueChange={(value) => onTabChange(value as TabType)}
              className="hidden shrink-0 lg:block"
            >
              <TabsList>
                <TabsTrigger value="document-explorer">Document Explorer</TabsTrigger>
                <TabsTrigger value="references" className="relative">
                  References
                  <Badge className="h-4.5 min-w-4.5 rounded-full" variant="secondary">
                    {referenceExtraction?.state?.extracted_references?.length || 0}
                  </Badge>
                  {needsReferenceReview && (
                    <span className="ring-background absolute -top-1 -right-1 size-2.5 rounded-full bg-amber-500 ring-2" />
                  )}
                </TabsTrigger>
                <TabsTrigger value="files">
                  Files
                  <Badge className="h-4.5 min-w-4.5 rounded-full" variant="secondary">
                    {projectDetail.files?.length ?? 0}
                  </Badge>
                </TabsTrigger>
                <TabsTrigger value="analyses">
                  Assessments
                  <Badge className="h-4.5 min-w-4.5 rounded-full" variant="secondary">
                    {results.filter((r) => isWorkflowTypeVisible(r.run.type)).length}
                  </Badge>
                </TabsTrigger>
                <TabsTrigger value="peer-review" className="relative">
                  Peer Review
                  {peerReviewFacts.memos.length > 0 && (
                    <Badge className="h-4.5 min-w-4.5 rounded-full" variant="secondary">
                      {peerReviewFacts.memos.length}
                    </Badge>
                  )}
                  {peerReviewAttention && (
                    <span className="ring-background absolute -top-1 -right-1 size-2.5 rounded-full bg-amber-500 ring-2" />
                  )}
                </TabsTrigger>
              </TabsList>
            </Tabs>

            {/* Share badge, revision switcher, Download DOCX and the overflow menu. */}
            <div className="ml-auto flex shrink-0 items-center gap-2">
              {readOnly && (
                <Badge variant="secondary" className="h-7 text-xs">
                  Read-only view
                </Badge>
              )}
              <AnalysisOptionsMenu
                project={projectDetail.project}
                results={results}
                readOnly={readOnly}
                selectedRevision={selectedRevision}
                onRevisionChange={onRevisionChange}
                onRevisionCreated={onRevisionCreated}
                downloadLabel="Export"
              />
            </div>
          </header>

          {needsReferenceReview && (
            <div className="flex shrink-0 flex-wrap items-center gap-3 border-b bg-amber-50 px-3 py-2 dark:bg-amber-950/30">
              <BookOpen className="size-4 shrink-0 text-amber-700 dark:text-amber-400" />
              <p className="min-w-0 text-sm">
                <strong className="font-medium">Reference review required.</strong>{' '}
                <span className="text-muted-foreground">
                  Upload source documents or fetch them from the web, then approve to start the assessment.
                </span>
              </p>
              <div className="ml-auto flex shrink-0 items-center gap-2">
                <Button size="sm" variant="outline" className="h-7" onClick={() => onTabChange('references')}>
                  Review references
                </Button>
                <Button
                  size="sm"
                  className="h-7"
                  onClick={referenceApproval.handleApprove}
                  disabled={referenceApproval.isApproveDisabled}
                >
                  {referenceApproval.showApproveButtonSpinner && (
                    <Loader2 className="mr-2 size-4 animate-spin" aria-hidden />
                  )}
                  {referenceApproval.approveButtonText}
                </Button>
              </div>
              <UnmatchedReferencesApproveDialog
                open={referenceApproval.showUnmatchedWarning}
                onOpenChange={referenceApproval.setShowUnmatchedWarning}
                unmatchedCount={referenceApproval.unmatchedCount}
                onConfirmApprove={referenceApproval.handleConfirmApprove}
              />
            </div>
          )}

          <div className="min-h-0 flex-1">
            {activeTab === 'document-explorer' ? (
              children
            ) : (
              /* Placeholder framing for tabs that have not been redesigned yet:
                 they were built for a scrolling page inside a max-width column. */
              <div className="h-full overflow-y-auto">
                <div className="mx-auto h-full max-w-7xl p-4">{children}</div>
              </div>
            )}
          </div>
        </div>
      </ProjectViewProvider>
    </ProjectFeedbackProvider>
  );
}
