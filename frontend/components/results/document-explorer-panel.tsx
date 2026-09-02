'use client';

import { useProjectView } from '@/components/results/project-view-context';
import { DocumentExplorerTab } from './document-explorer/document-explorer-tab';

/**
 * The document explorer as a tab panel. Everything around it — title, tabs,
 * revision switcher, the banners — comes from ProjectShell.
 */
export function DocumentExplorerPanel() {
  const { projectDetail, readOnly, navigateToTab } = useProjectView();

  return (
    <DocumentExplorerTab
      projectDetail={projectDetail}
      // The shell's read-only covers older revisions as well as projects that
      // aren't the reader's, which is what starting a run has to answer to:
      // the start API targets the project's current revision, not the one on
      // screen. Rating and resolving issues is a separate question, answered
      // inside the tab by the access level.
      canRunAssessments={!readOnly}
      onNavigateToAnalyses={() => navigateToTab('analyses')}
    />
  );
}
