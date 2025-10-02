'use client';

import { useClaimFeedback } from '../hooks/use-claim-feedback';
import { CollapsibleFeedback } from './collapsible-feedback';
import {
  ClaimSubstantiationResultWithClaimIndex,
  Citation,
  BibliographyItem,
  ClaimCommonKnowledgeResultWithClaimIndex,
} from '@/lib/generated-api';

interface FeedbackSectionProps {
  commonKnowledgeResult: ClaimCommonKnowledgeResultWithClaimIndex;
  substantiation: ClaimSubstantiationResultWithClaimIndex;
  citations: Citation[];
  references: BibliographyItem[];
  feedback: string;
  className?: string;
}

export function FeedbackSection({
  commonKnowledgeResult,
  substantiation,
  citations,
  references,
  feedback,
  className = '',
}: FeedbackSectionProps) {
  const { shouldMinimize, isExpanded, setIsExpanded } = useClaimFeedback({
    commonKnowledgeResult,
    substantiation,
    citations,
    references,
  });

  const feedbackContent = (
    <p className="text-xs text-muted-foreground">
      <strong>Feedback:</strong> {feedback}
    </p>
  );

  return (
    <CollapsibleFeedback
      shouldMinimize={shouldMinimize}
      isExpanded={isExpanded}
      onToggle={() => setIsExpanded(!isExpanded)}
      buttonText="Show feedback details"
      className={`mt-1 ${className}`}
      expandedContent={feedbackContent}
    >
      {feedbackContent}
    </CollapsibleFeedback>
  );
}
