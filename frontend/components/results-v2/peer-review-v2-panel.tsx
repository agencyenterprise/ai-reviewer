'use client';

import { useProjectView } from '@/components/results/project-view-context';
import { PeerReviewTabV2 } from './peer-review/peer-review-tab';

/** Hash format the document explorer understands: `#L5` or `#L5-12`. */
function lineRangeHash(lineRange?: [number, number]): string | undefined {
  if (!lineRange) return undefined;
  const [start, end] = lineRange;
  return start === end ? `#L${start}` : `#L${start}-${end}`;
}

/** The v2 peer review tab as a tab panel, taking its project from the shell. */
export function PeerReviewV2Panel() {
  const { projectDetail, readOnly, onRevisionChange, onRevisionCreated, navigateToTab } = useProjectView();

  return (
    <PeerReviewTabV2
      projectDetail={projectDetail}
      readOnly={readOnly}
      onRevisionChange={onRevisionChange}
      onRevisionCreated={onRevisionCreated}
      onNavigateToDocumentExplorer={(lineRange) => navigateToTab('document-explorer', lineRangeHash(lineRange))}
    />
  );
}
