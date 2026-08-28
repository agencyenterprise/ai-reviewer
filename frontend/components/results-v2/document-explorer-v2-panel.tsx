'use client';

import { useProjectView } from '@/components/results/project-view-context';
import { DocumentExplorerTabV2 } from './document-explorer/document-explorer-tab';

/**
 * The v2 document explorer as a tab panel. Everything around it — title, tabs,
 * revision switcher, reference-review banner — comes from ProjectResultsShell,
 * exactly as it does for the production tabs, so the two routes differ only in
 * the explorer itself.
 */
export function DocumentExplorerV2Panel() {
  const { projectDetail, readOnly, selectedRevision, onRevisionChange, navigateToTab } = useProjectView();

  return (
    <DocumentExplorerTabV2
      projectDetail={projectDetail}
      readOnly={readOnly}
      onNavigateToAnalyses={() => navigateToTab('analyses')}
      selectedRevision={selectedRevision}
      onRevisionChange={onRevisionChange}
    />
  );
}
