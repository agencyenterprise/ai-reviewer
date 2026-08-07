'use client';

import { EmptyState } from '@/components/shared/empty-state';
import { Button } from '@/components/ui/button';
import { MessagesSquare, Upload } from 'lucide-react';

interface PeerReviewEmptyStateProps {
  readOnly: boolean;
  onUploadMemos: () => void;
}

/**
 * Zero state. The tab is always visible, so on a project that never goes
 * through peer review this has to teach rather than nag.
 */
export function PeerReviewEmptyState({ readOnly, onUploadMemos }: PeerReviewEmptyStateProps) {
  return (
    <EmptyState
      icon={MessagesSquare}
      title="No reviewer memos yet"
      description="Once your draft comes back from peer review, upload the reviewers' memos here. Draft Detective will turn their points into a revision plan, then — after you upload your revised draft — draft a response memo per reviewer and a coverage report for a QA manager."
    >
      {!readOnly && (
        <Button onClick={onUploadMemos}>
          <Upload className="size-4" />
          Upload reviewer memos
        </Button>
      )}
    </EmptyState>
  );
}
