'use client';

import * as React from 'react';
import { classifyClaim, ClaimCategory } from '@/lib/claim-classification';
import {
  Claim,
  ClaimSubstantiationResultWithClaimIndex,
  Citation,
  BibliographyItem,
  ClaimCommonKnowledgeResultWithClaimIndex,
} from '@/lib/generated-api';

interface UseClaimFeedbackProps {
  claim: Claim;
  commonKnowledgeResult: ClaimCommonKnowledgeResultWithClaimIndex;
  substantiation: ClaimSubstantiationResultWithClaimIndex;
  citations: Citation[];
  references: BibliographyItem[];
}

interface UseClaimFeedbackReturn {
  claimCategory: ClaimCategory;
  shouldMinimize: boolean;
  isExpanded: boolean;
  setIsExpanded: (value: boolean) => void;
  showCommonKnowledgeRationale: boolean;
}

export function useClaimFeedback({
  claim,
  commonKnowledgeResult,
  substantiation,
  citations,
  references,
}: UseClaimFeedbackProps): UseClaimFeedbackReturn {
  const claimCategory = classifyClaim(commonKnowledgeResult, substantiation, citations, references);

  // Minimize if it's marked as probably common knowledge OR if it's marked as common knowledge at all
  const shouldMinimize =
    claimCategory === ClaimCategory.PROBABLY_COMMON_KNOWLEDGE || Boolean(commonKnowledgeResult.isCommonKnowledge);
  const [isExpanded, setIsExpanded] = React.useState(!shouldMinimize);

  const showCommonKnowledgeRationale = Boolean(
    commonKnowledgeResult.rationale && commonKnowledgeResult.isCommonKnowledge,
  );

  return {
    claimCategory,
    shouldMinimize,
    isExpanded,
    setIsExpanded,
    showCommonKnowledgeRationale,
  };
}
