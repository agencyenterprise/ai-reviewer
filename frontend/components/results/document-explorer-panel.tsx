'use client';

import { useProjectView } from '@/components/results/project-view-context';
import { DocumentExplorerTab } from './document-explorer/document-explorer-tab';

/**
 * The document explorer as a tab panel. Everything around it — title, tabs,
 * revision switcher, the banners — comes from ProjectShell.
 */
export function DocumentExplorerPanel() {
  const { projectDetail, navigateToTab } = useProjectView();

  return <DocumentExplorerTab projectDetail={projectDetail} onNavigateToAnalyses={() => navigateToTab('analyses')} />;
}
