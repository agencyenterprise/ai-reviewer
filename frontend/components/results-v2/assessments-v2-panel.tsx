'use client';

import { useProjectView } from '@/components/results/project-view-context';
import { useDocumentExplorerStore } from '@/lib/stores/document-explorer-store';
import { AssessmentsTabV2 } from './assessments/assessments-tab';

/** Hash format the document explorer understands: `#L5` or `#L5-12`. */
function lineRangeHash(lineRange?: [number, number]): string | undefined {
  if (!lineRange) return undefined;
  const [start, end] = lineRange;
  return start === end ? `#L${start}` : `#L${start}-${end}`;
}

/** The v2 assessments tab as a tab panel, taking its project from the shell. */
export function AssessmentsV2Panel() {
  const { projectDetail, readOnly, navigateToTab } = useProjectView();
  const setFilter = useDocumentExplorerStore((s) => s.setFilter);

  return (
    <AssessmentsTabV2
      projectDetail={projectDetail}
      readOnly={readOnly}
      onNavigateToDocumentExplorer={(lineRange) => {
        setFilter({ workflowType: [] });
        navigateToTab('document-explorer', lineRangeHash(lineRange));
      }}
      onNavigateToReferences={() => navigateToTab('references')}
      onNavigateToPeerReview={() => navigateToTab('peer-review')}
    />
  );
}
