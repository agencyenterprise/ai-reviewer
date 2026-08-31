'use client';

import { useProjectView } from '@/components/results/project-view-context';
import { DocumentExplorerTabV2 } from './document-explorer/document-explorer-tab';

/**
 * The v2 document explorer as a tab panel. Everything around it — title, tabs,
 * revision switcher, the banners — comes from ProjectResultsShell,
 * exactly as it does for the production tabs, so the two routes differ only in
 * the explorer itself.
 */
export function DocumentExplorerV2Panel() {
  const { projectDetail, navigateToTab } = useProjectView();

  return <DocumentExplorerTabV2 projectDetail={projectDetail} onNavigateToAnalyses={() => navigateToTab('analyses')} />;
}
