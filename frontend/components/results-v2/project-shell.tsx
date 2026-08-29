'use client';

import { AnalysisOptionsMenu } from '@/components/results/components/analysis-options-menu';
import { TabType } from '@/components/results/constants';
import { ProjectViewProvider } from '@/components/results/project-view-context';
import {
  derivePeerReviewFacts,
  peerReviewNeedsAttention,
} from '@/components/results/tabs/peer-review/peer-review-derive';
import { Badge } from '@/components/ui/badge';
import { EditableTitle } from '@/components/ui/editable-title';
import { useExperimentalFeatures } from '@/context/experimental-features-context';
import { ProjectFeedbackProvider } from '@/lib/contexts/project-feedback-context';
import { ProjectDetailed, WorkflowRunType } from '@/lib/generated-api';
import { useWorkflowTypes } from '@/lib/hooks/use-workflow-types';
import { getWorkflowRunByType } from '@/lib/workflow-state';
import { ReactNode, useMemo } from 'react';
import { AppBar } from './app-bar';
import { NewAssessmentButton } from './new-assessment-button';
import { OldRevisionBanner } from './old-revision-banner';
import { ProjectTab, ProjectTabs } from './project-tabs';
import { ReferenceReviewBanner } from './reference-review-banner';

/** Tabs redesigned for the v2 frame, which manage their own scrolling. */
/** Every redesigned tab manages its own scrolling; only Summary still does not. */
const FULL_BLEED_TABS = new Set<TabType>(['document-explorer', 'references', 'files', 'analyses', 'peer-review']);

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

  const currentRevision = projectDetail.project.current_revision ?? 1;
  const referenceExtraction = getWorkflowRunByType(results, WorkflowRunType.ReferenceExtraction);

  const { showExperimentalFeatures } = useExperimentalFeatures();
  const peerReviewFacts = derivePeerReviewFacts(projectDetail);
  const peerReviewAttention = peerReviewNeedsAttention(peerReviewFacts, readOnly);

  const tabs: ProjectTab[] = [
    { id: 'document-explorer', label: 'Document Explorer' },
    {
      id: 'references',
      label: 'References',
      count: referenceExtraction?.state?.extracted_references?.length || 0,
      attention: needsReferenceReview,
    },
    { id: 'files', label: 'Files', count: projectDetail.files?.length ?? 0 },
    { id: 'analyses', label: 'Assessments', count: results.filter((r) => isWorkflowTypeVisible(r.run.type)).length },
    // Peer Review is still alpha, so it only exists for users who opted in.
    ...(showExperimentalFeatures
      ? [
          {
            id: 'peer-review' as const,
            label: 'Peer Review',
            count: peerReviewFacts.memos.length > 0 ? peerReviewFacts.memos.length : undefined,
            attention: peerReviewAttention,
          },
        ]
      : []),
  ];

  const titleNode =
    !readOnly && onTitleSave ? (
      <EditableTitle
        title={projectDetail.project.title}
        titleClassName="text-sm font-semibold truncate min-w-0"
        className="min-w-0"
        onSave={onTitleSave}
        isLoading={isTitleSaving}
      />
    ) : (
      <h1 className="truncate text-sm font-semibold">{projectDetail.project.title}</h1>
    );

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
          <AppBar title={titleNode} />

          {/* This project: the ways in on the left, what you can do with it on
              the right. The title names the project a row above. */}
          <header className="flex h-12 shrink-0 items-center gap-3 border-b px-3">
            <ProjectTabs tabs={tabs} activeTab={activeTab} onTabChange={onTabChange} />

            {/* Share badge, revision switcher, Export and the overflow menu. */}
            <div className="ml-auto flex shrink-0 items-center gap-2">
              {readOnly && (
                <Badge variant="secondary" className="h-7 text-xs">
                  Read-only view
                </Badge>
              )}
              {!readOnly && <NewAssessmentButton projectId={projectDetail.project.id} />}
              <AnalysisOptionsMenu
                project={projectDetail.project}
                results={results}
                readOnly={readOnly}
                selectedRevision={selectedRevision}
                onRevisionChange={onRevisionChange}
                onRevisionCreated={onRevisionCreated}
                downloadLabel="Export"
                downloadVariant="outline"
                compact
              />
            </div>
          </header>

          {needsReferenceReview && (
            <ReferenceReviewBanner projectDetail={projectDetail} onReviewReferences={() => onTabChange('references')} />
          )}

          {/* An older revision governs every tab, not just the document, so the
              notice belongs to the view rather than to the reader. */}
          {selectedRevision != null && selectedRevision < currentRevision && (
            <OldRevisionBanner
              selectedRevision={selectedRevision}
              currentRevision={currentRevision}
              onViewCurrent={onRevisionChange ? () => onRevisionChange(currentRevision) : undefined}
            />
          )}

          <div className="min-h-0 flex-1">
            {FULL_BLEED_TABS.has(activeTab) ? (
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
