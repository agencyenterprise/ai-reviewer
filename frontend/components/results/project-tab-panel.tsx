'use client';

import { useExperimentalFeatures } from '@/context/experimental-features-context';
import { WorkflowRunType } from '@/lib/generated-api';
import { useDocumentExplorerStore } from '@/lib/stores/document-explorer-store';
import { TabType } from './constants';
import { useProjectView } from './project-view-context';
import { AnalysesTab, FilesTab, PeerReviewTab, ReferenceReviewTab, SummaryTab } from './tabs';
import { DocumentExplorerTab } from './tabs/document-explorer-tab';

/** Hash format understood by the document explorer: `#L5` or `#L5-12`. */
function lineRangeHash(lineRange?: [number, number]): string | undefined {
  if (!lineRange) return undefined;
  const [start, end] = lineRange;
  return start === end ? `#L${start}` : `#L${start}-${end}`;
}

/** Renders a single project tab, sourcing shared state from the surrounding shell. */
export function ProjectTabPanel({ tab }: { tab: TabType }) {
  const { projectDetail, readOnly, selectedRevision, onRevisionChange, onRevisionCreated, navigateToTab } =
    useProjectView();
  const setFilter = useDocumentExplorerStore((s) => s.setFilter);
  // Peer Review is still alpha: the tab, and the route behind it, exist only
  // for users who opted in.
  const { showExperimentalFeatures, isLoading: isLoadingPreferences } = useExperimentalFeatures();

  const navigateToDocumentExplorer = (lineRange?: [number, number]) => {
    navigateToTab('document-explorer', lineRangeHash(lineRange));
  };

  const navigateToDocumentExplorerFiltered = (workflowType?: WorkflowRunType) => {
    if (workflowType) {
      setFilter({ workflowType: [workflowType] });
    }
    navigateToTab('document-explorer');
  };

  switch (tab) {
    case 'summary':
      return (
        <SummaryTab
          projectDetail={projectDetail}
          onNavigateToAnalyses={() => navigateToTab('analyses')}
          onNavigateToDocumentExplorer={navigateToDocumentExplorerFiltered}
        />
      );
    case 'files':
      return <FilesTab projectDetail={projectDetail} readOnly={readOnly} onRevisionCreated={onRevisionCreated} />;
    case 'document-explorer':
      return (
        <DocumentExplorerTab
          projectDetail={projectDetail}
          onNavigateToAnalyses={() => navigateToTab('analyses')}
          selectedRevision={selectedRevision}
          onRevisionChange={onRevisionChange}
        />
      );
    case 'references':
      return <ReferenceReviewTab projectId={projectDetail.project.id} readOnly={readOnly} />;
    case 'analyses':
      return (
        <AnalysesTab
          projectDetail={projectDetail}
          readOnly={readOnly}
          onNavigateToDocumentExplorer={navigateToDocumentExplorer}
          onNavigateToReferences={() => navigateToTab('references')}
          onNavigateToPeerReview={showExperimentalFeatures ? () => navigateToTab('peer-review') : undefined}
        />
      );
    case 'peer-review':
      if (isLoadingPreferences) return null;
      if (!showExperimentalFeatures) return <PeerReviewUnavailable />;
      return (
        <PeerReviewTab
          projectDetail={projectDetail}
          readOnly={readOnly}
          onRevisionChange={onRevisionChange}
          onRevisionCreated={onRevisionCreated}
          onNavigateToDocumentExplorer={navigateToDocumentExplorer}
        />
      );
  }
}

/**
 * Shown when the Peer Review route is reached without the alpha opt-in — from a
 * bookmark or a shared link, since the tab itself is hidden in that case.
 */
function PeerReviewUnavailable() {
  return (
    <div className="py-12 text-center text-sm text-muted-foreground">
      Peer Review is an alpha feature. Turn on <strong>Alpha features</strong> in your profile menu to use it.
    </div>
  );
}
