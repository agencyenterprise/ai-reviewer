'use client';

import { UnmatchedReferencesApproveDialog } from '@/components/results/tabs/reference-review/unmatched-references-approve-dialog';
import { useReferenceApprovalFlow } from '@/components/results/tabs/reference-review/use-reference-approval-flow';
import { Button } from '@/components/ui/button';
import { ProjectDetailed } from '@/lib/generated-api';
import { BookOpen, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { HelpCenter } from '@/components/help/help-center';

interface ReferenceReviewBannerProps {
  projectDetail: ProjectDetailed;
  onReviewReferences: () => void;
}

/**
 * The strip that appears while Claim Reference Validation is waiting to be let
 * through. It names the assessment rather than saying "review required",
 * because the reason a project stalls here is not obvious from the tabs: every
 * other assessment reads the document alone and keeps producing results.
 */
export function ReferenceReviewBanner({ projectDetail, onReviewReferences }: ReferenceReviewBannerProps) {
  const approval = useReferenceApprovalFlow(projectDetail, projectDetail.project.id);
  const [showExplanation, setShowExplanation] = useState(false);

  return (
    <div className="flex shrink-0 flex-wrap items-center gap-3 border-b bg-amber-50 px-3 py-2 dark:bg-amber-950/30">
      <BookOpen className="size-4 shrink-0 text-amber-700 dark:text-amber-400" />
      <p className="min-w-0 text-sm">
        <strong className="font-medium">Reference review required.</strong>{' '}
        <span className="text-muted-foreground">
          Claim Reference Validation reads each citation against the source it cites, and needs those sources first.
        </span>{' '}
        <button
          onClick={() => setShowExplanation(true)}
          className="cursor-pointer text-muted-foreground underline underline-offset-2 hover:text-foreground"
        >
          Why this is needed
        </button>
      </p>

      <div className="ml-auto flex shrink-0 items-center gap-2">
        <Button size="xs" variant="outline" className="h-6" onClick={onReviewReferences}>
          Review references
        </Button>
        <Button size="xs" className="h-6" onClick={approval.handleApprove} disabled={approval.isApproveDisabled}>
          {approval.showApproveButtonSpinner && <Loader2 className="size-3 animate-spin" aria-hidden />}
          {approval.approveButtonText}
        </Button>
      </div>

      <UnmatchedReferencesApproveDialog
        open={approval.showUnmatchedWarning}
        onOpenChange={approval.setShowUnmatchedWarning}
        unmatchedCount={approval.unmatchedCount}
        onConfirmApprove={approval.handleConfirmApprove}
      />

      <HelpCenter
        open={showExplanation}
        onOpenChange={setShowExplanation}
        topic="source-files"
        onReviewReferences={() => {
          setShowExplanation(false);
          onReviewReferences();
        }}
      />
    </div>
  );
}
