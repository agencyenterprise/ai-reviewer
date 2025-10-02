'use client';

import {
  ClaimSubstantiationResultWithClaimIndex,
  Citation,
  BibliographyItem,
  ClaimCommonKnowledgeResultWithClaimIndex,
  Severity,
  ToulminClaim,
} from '@/lib/generated-api';
import { ChunkItem } from './chunk-display';
import { ClaimCategoryLabel } from './claim-category-label';
import { SeverityBadge } from './severity-badge';
import { CommonKnowledgeBadge } from './common-knowledge-badge';
import { CommonKnowledgeAccordion } from './common-knowledge-accordion';
import { SubstantiationResults } from './substantiation-results';
import { cn } from '@/lib/utils';
import { classifyClaim } from '@/lib/claim-classification';
import { ToulminClaimAccordion } from './toulmin-claim-accordion';

export interface ClaimAnalysisCardProps {
  claim: ToulminClaim;
  commonKnowledgeResult?: ClaimCommonKnowledgeResultWithClaimIndex;
  substantiation?: ClaimSubstantiationResultWithClaimIndex;
  citations: Citation[];
  references: BibliographyItem[];
  className?: string;
}

export function ClaimAnalysisCard({
  claim,
  commonKnowledgeResult,
  substantiation,
  citations,
  references,
  className,
}: ClaimAnalysisCardProps) {
  // Calculate derived values inside the component
  const isUnsubstantiated = substantiation ? !substantiation.isSubstantiated : false;
  const isCommonKnowledge = commonKnowledgeResult?.isCommonKnowledge || false;
  const needsSubstantiation = commonKnowledgeResult?.needsSubstantiation || false;
  const claimCategory = classifyClaim(
    commonKnowledgeResult || {
      chunkIndex: 0,
      claimIndex: 0,
      isCommonKnowledge: false,
      needsSubstantiation: false,
      commonKnowledgeRationale: '',
      substantiationRationale: '',
      claimTypes: [],
      commonKnowledgeTypes: [],
    },
    substantiation || {
      chunkIndex: 0,
      claimIndex: 0,
      isSubstantiated: false,
      rationale: '',
      feedback: '',
      severity: Severity.NUMBER_0,
    },
    citations,
    references,
  );
  const severity = substantiation ? substantiation.severity : Severity.NUMBER_0;

  // Determine background color based on substantiation and common knowledge status
  const getBackgroundColor = () => {
    if (isUnsubstantiated) {
      if (needsSubstantiation && isCommonKnowledge) {
        return 'bg-orange-50/40';
      }
      return 'bg-red-50/40';
    }
    return '';
  };

  return (
    <ChunkItem className={cn(getBackgroundColor(), 'space-y-2', className)}>
      {/* Claim Metadata */}
      <div className="flex items-center gap-1">
        <ClaimCategoryLabel category={claimCategory} />
        <SeverityBadge severity={severity} />
        <CommonKnowledgeBadge
          isCommonKnowledge={commonKnowledgeResult?.isCommonKnowledge || false}
          commonKnowledgeRationale={commonKnowledgeResult?.commonKnowledgeRationale}
          claimCategory={claimCategory}
        />
      </div>

      {/* Claim */}
      <ToulminClaimAccordion claim={claim} />

      {/* Common Knowledge Analysis */}
      {commonKnowledgeResult && <CommonKnowledgeAccordion result={commonKnowledgeResult} />}

      {/* Substantiation Results */}
      <SubstantiationResults substantiation={substantiation} commonKnowledgeResult={commonKnowledgeResult} />
    </ChunkItem>
  );
}
