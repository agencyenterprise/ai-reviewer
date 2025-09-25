'use client';

import { useClaimFeedback } from '../hooks/use-claim-feedback';
import { CollapsibleFeedback } from './collapsible-feedback';
import { Claim, ClaimSubstantiationResultWithClaimIndex, Citation, BibliographyItem } from '@/lib/generated-api';

interface UnsubstantiatedFeedbackProps {
  claim: Claim;
  substantiation: ClaimSubstantiationResultWithClaimIndex;
  citations: Citation[];
  references: BibliographyItem[];
  className?: string;
}

export function UnsubstantiatedFeedback({
  claim,
  substantiation,
  citations,
  references,
  className = '',
}: UnsubstantiatedFeedbackProps) {
  const { shouldMinimize, isExpanded, setIsExpanded, showCommonKnowledgeRationale } = useClaimFeedback({
    claim,
    substantiation,
    citations,
    references,
  });

  const substantiationContent = (
    <>
      <p className="text-sm text-red-600">
        <strong>Unsubstantiated because:</strong> {substantiation.rationale}
      </p>
      {substantiation.feedback && (
        <p className="text-sm text-blue-600 mt-1">
          <strong>Feedback to resolve:</strong> {substantiation.feedback}
        </p>
      )}
    </>
  );

  return (
    <CollapsibleFeedback
      shouldMinimize={shouldMinimize}
      isExpanded={isExpanded}
      onToggle={() => setIsExpanded(!isExpanded)}
      buttonText="Show substantiation details"
      className={className}
      children={
        <>
          {showCommonKnowledgeRationale && (
            <div
              className={`mb-2 p-2 ${shouldMinimize ? 'bg-amber-50 border-amber-200' : 'bg-blue-50 border-blue-200'} border rounded text-xs`}
            >
              <p className={`font-medium ${shouldMinimize ? 'text-amber-800' : 'text-blue-800'} mb-1`}>
                Common Knowledge Assessment:
              </p>
              <p className={shouldMinimize ? 'text-amber-700' : 'text-blue-700'}>
                {substantiation.commonKnowledgeRationale}
              </p>
            </div>
          )}
          {!shouldMinimize && substantiationContent}
        </>
      }
      expandedContent={substantiationContent}
    />
  );
}
