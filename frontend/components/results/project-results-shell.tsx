'use client';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Callout } from '@/components/ui/callout';
import { EditableTitle } from '@/components/ui/editable-title';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useExperimentalFeatures } from '@/context/experimental-features-context';
import { ProjectFeedbackProvider } from '@/lib/contexts/project-feedback-context';
import { ProjectDetailed, WorkflowRunType } from '@/lib/generated-api';
import { useWorkflowTypes } from '@/lib/hooks/use-workflow-types';
import { cn } from '@/lib/utils';
import { getWorkflowRunByType } from '@/lib/workflow-state';
import { format } from 'date-fns';
import { BookOpen, Loader2 } from 'lucide-react';
import { ReactNode, useMemo, useState } from 'react';
import { AnalysisOptionsMenu } from './components/analysis-options-menu';
import { TabType } from './constants';
import { ProjectViewProvider } from './project-view-context';
import { derivePeerReviewFacts, peerReviewNeedsAttention } from './tabs/peer-review/peer-review-derive';
import { PageTitle } from '@/components/shared/page-title';
import { HelpCenter } from '@/components/help/help-center';
import { UnmatchedReferencesApproveDialog } from './tabs/reference-review/unmatched-references-approve-dialog';
import { useReferenceApprovalFlow } from './tabs/reference-review/use-reference-approval-flow';

interface ProjectResultsShellProps {
  projectDetail: ProjectDetailed;
  /** Tab currently shown in `children` */
  activeTab: TabType;
  /** Switch to another tab, optionally landing on a URL hash (e.g. `#L5-12`) */
  onTabChange: (tab: TabType, hash?: string) => void;
  /** When true, hides edit/action controls (for shared view) */
  readOnly?: boolean;
  /** Callback for saving title (only used when readOnly=false) */
  onTitleSave?: (newTitle: string) => Promise<void>;
  /** Whether title is currently being saved */
  isTitleSaving?: boolean;
  /** When true, shows the reference review banner indicating approval is needed */
  needsReferenceReview?: boolean;
  /** Currently displayed revision */
  selectedRevision?: number;
  /** Callback when user switches revision */
  onRevisionChange?: (revision: number) => void;
  /** Callback after a new revision is created, to follow it in the view */
  onRevisionCreated?: () => void;
  /** Content of the active tab */
  children: ReactNode;
}

/**
 * Chrome around a project's tabs: title, reference-review banner, tab list and options menu.
 * The active tab's content is rendered as `children` so it can come from a route segment.
 */
export function ProjectResultsShell({
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
}: ProjectResultsShellProps) {
  const results = projectDetail.workflow_runs ?? [];

  const documentProcessing = getWorkflowRunByType(results, WorkflowRunType.DocumentProcessing);
  const documentSummarization = getWorkflowRunByType(results, WorkflowRunType.DocumentSummarization);
  const referenceExtraction = getWorkflowRunByType(results, WorkflowRunType.ReferenceExtraction);
  const { isWorkflowTypeVisible } = useWorkflowTypes();
  // Peer Review is still alpha, so it only exists for users who opted in.
  const { showExperimentalFeatures } = useExperimentalFeatures();

  const referenceApproval = useReferenceApprovalFlow(projectDetail, projectDetail.project.id);
  const [showExplanation, setShowExplanation] = useState(false);

  // Find the main document summary from the summaries list
  const mainFileId = documentProcessing?.state?.file?.file_id;
  const mainSummary = documentSummarization?.state?.summaries?.find((s) => s.file_id === mainFileId);
  const authors = mainSummary?.authors;

  const peerReviewFacts = derivePeerReviewFacts(projectDetail);
  const peerReviewAttention = peerReviewNeedsAttention(peerReviewFacts, readOnly);

  const projectView = useMemo(
    () => ({
      projectDetail,
      readOnly,
      selectedRevision,
      onRevisionChange,
      onRevisionCreated,
      navigateToTab: onTabChange,
    }),
    [projectDetail, readOnly, selectedRevision, onRevisionChange, onRevisionCreated, onTabChange],
  );

  return (
    <ProjectFeedbackProvider
      projectId={readOnly ? undefined : projectDetail.project.id}
      feedbackVisibility={readOnly ? null : (projectDetail.project.feedback_visibility ?? null)}
    >
      <PageTitle title={projectDetail.project.title} />

      <ProjectViewProvider value={projectView}>
        <div className="space-y-3">
          {/* Header */}
          <div className="flex items-center justify-between">
            <hgroup className="w-full space-y-1">
              {!readOnly && onTitleSave ? (
                <EditableTitle
                  title={projectDetail.project.title}
                  titleClassName="text-xl font-bold"
                  onSave={onTitleSave}
                  isLoading={isTitleSaving}
                />
              ) : (
                <h1 className="text-xl font-bold">{projectDetail.project.title}</h1>
              )}
              <h2 className="text-muted-foreground text-sm">
                {authors && <span>{authors} — </span>}
                <span>Project created on {format(projectDetail.project.created_at || new Date(), 'MMM d, yyyy')}</span>
              </h2>
            </hgroup>
          </div>

          {needsReferenceReview && (
            <Callout variant="warning" icon={BookOpen} title="Reference review required">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm min-w-0">
                  Claim Reference Validation reads each citation against the source it cites, and needs those sources
                  first.{' '}
                  <button
                    onClick={() => setShowExplanation(true)}
                    className="cursor-pointer underline underline-offset-2"
                  >
                    Why this is needed
                  </button>
                </p>
                <div className="flex shrink-0 flex-wrap items-center gap-2">
                  <Button size="sm" variant="outline" onClick={() => onTabChange('references')}>
                    Review References
                  </Button>
                  <Button
                    size="sm"
                    onClick={referenceApproval.handleApprove}
                    disabled={referenceApproval.isApproveDisabled}
                  >
                    {referenceApproval.showApproveButtonSpinner && (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden />
                    )}
                    {referenceApproval.approveButtonText}
                  </Button>
                </div>
              </div>
              <UnmatchedReferencesApproveDialog
                open={referenceApproval.showUnmatchedWarning}
                onOpenChange={referenceApproval.setShowUnmatchedWarning}
                unmatchedCount={referenceApproval.unmatchedCount}
                onConfirmApprove={referenceApproval.handleConfirmApprove}
              />
              <HelpCenter
                open={showExplanation}
                onOpenChange={setShowExplanation}
                topic="source-files"
                onReviewReferences={() => {
                  setShowExplanation(false);
                  onTabChange('references');
                }}
              />
            </Callout>
          )}

          <div className="flex flex-col gap-2 md:items-center md:justify-between md:flex-row">
            <Tabs value={activeTab} onValueChange={(value) => onTabChange(value as TabType)}>
              <TabsList>
                <TabsTrigger value="document-explorer">Document Explorer</TabsTrigger>
                <TabsTrigger value="references" className="relative">
                  References{' '}
                  <Badge className="rounded-full h-4.5 min-w-4.5" variant="secondary">
                    {referenceExtraction?.state?.extracted_references?.length || 0}
                  </Badge>
                  {needsReferenceReview && (
                    <span className="absolute -top-1 -right-1 h-2.5 w-2.5 rounded-full bg-amber-500 ring-2 ring-background" />
                  )}
                </TabsTrigger>
                <TabsTrigger value="files">
                  Files{' '}
                  <Badge className="rounded-full h-4.5 min-w-4.5" variant="secondary">
                    {projectDetail.files?.length ?? 0}
                  </Badge>
                </TabsTrigger>
                <TabsTrigger value="analyses">
                  Assessments{' '}
                  <Badge className="rounded-full h-4.5 min-w-4.5" variant="secondary">
                    {results.filter((r) => isWorkflowTypeVisible(r.run.type)).length}
                  </Badge>
                </TabsTrigger>
                {showExperimentalFeatures && (
                  <TabsTrigger value="peer-review" className="relative">
                    Peer Review
                    {peerReviewFacts.memos.length > 0 && (
                      <Badge className="rounded-full h-4.5 min-w-4.5" variant="secondary">
                        {peerReviewFacts.memos.length}
                      </Badge>
                    )}
                    {peerReviewAttention && (
                      <span className="absolute -top-1 -right-1 h-2.5 w-2.5 rounded-full bg-amber-500 ring-2 ring-background" />
                    )}
                  </TabsTrigger>
                )}
              </TabsList>
            </Tabs>

            <div className="flex items-center gap-2">
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
              />
            </div>
          </div>

          <div
            className={cn('border rounded-lg shadow-sm p-4', {
              'h-[calc(100vh-13rem)] p-0': activeTab === 'document-explorer',
            })}
          >
            {children}
          </div>
        </div>
      </ProjectViewProvider>
    </ProjectFeedbackProvider>
  );
}
