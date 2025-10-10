'use client';

import { AiGeneratedLabel } from '@/components/ai-generated-label';
import { Card, CardContent } from '@/components/ui/card';
import {
  ClaimCommonKnowledgeResultWithClaimIndex,
  ClaimSubstantiationResultWithClaimIndex,
  ToulminClaim,
} from '@/lib/generated-api';
import { CommonKnowledgeAccordion } from './common-knowledge-accordion';
import { SubstantiationResults } from './substantiation-results';
import { ToulminClaimAccordion } from './toulmin-claim-accordion';

export interface ClaimAnalysisCardProps {
  claim: ToulminClaim;
  commonKnowledgeResult?: ClaimCommonKnowledgeResultWithClaimIndex;
  substantiation?: ClaimSubstantiationResultWithClaimIndex;
  claimIndex: number;
  totalClaims: number;
}

export function ClaimAnalysisCard({
  claim,
  commonKnowledgeResult,
  substantiation,
  claimIndex,
  totalClaims,
}: ClaimAnalysisCardProps) {
  return (
    <Card>
      <CardContent className="space-y-4 py-0">
        <AiGeneratedLabel className="float-right" />
        <p className="text-sm font-medium">
          Claim {claimIndex + 1} of {totalClaims}
        </p>

        <p className="italic text-center text-base mb-5">&quot;{claim.text}&quot;</p>

        <p>
          <span className="font-medium">Extracted Claim: </span>
          {claim.claim}
        </p>

        <ToulminClaimAccordion claim={claim} />
        {commonKnowledgeResult && <CommonKnowledgeAccordion result={commonKnowledgeResult} />}
        {substantiation && <SubstantiationResults substantiation={substantiation} />}
      </CardContent>
    </Card>
  );
}
