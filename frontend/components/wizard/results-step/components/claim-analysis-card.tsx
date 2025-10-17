'use client';

import { AiGeneratedLabel } from '@/components/ai-generated-label';
import { Card, CardContent } from '@/components/ui/card';
import {
  BibliographyItem,
  ClaimCommonKnowledgeResultWithClaimIndex,
  ClaimSubstantiationResultWithClaimIndex,
  FileDocument,
  ToulminClaim,
} from '@/lib/generated-api';
import { CommonKnowledgeAccordion } from './common-knowledge-accordion';
import { RetrievedPassagesDisplay } from './retrieved-passages-display';
import { SubstantiationResults } from './substantiation-results';
import { ToulminClaimAccordion } from './toulmin-claim-accordion';

export interface ClaimAnalysisCardProps {
  claim: ToulminClaim;
  commonKnowledgeResult?: ClaimCommonKnowledgeResultWithClaimIndex;
  substantiation?: ClaimSubstantiationResultWithClaimIndex;
  references: BibliographyItem[];
  claimIndex: number;
  totalClaims: number;
  supportingFiles: FileDocument[];
}

export function ClaimAnalysisCard({
  claim,
  commonKnowledgeResult,
  substantiation,
  references,
  supportingFiles,
  claimIndex,
  totalClaims,
}: ClaimAnalysisCardProps) {
  return (
    <Card>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="font-medium">
            Claim Analysis - {claimIndex + 1} of {totalClaims}
          </p>
          <AiGeneratedLabel />
        </div>

        <p className="italic text-center">&quot;{claim.text}&quot;</p>

        <p>
          <span className="font-medium">Extracted Claim: </span>
          {claim.claim}
        </p>

        <div className="space-y-2">
          <ToulminClaimAccordion claim={claim} />
          {commonKnowledgeResult && <CommonKnowledgeAccordion result={commonKnowledgeResult} />}
          {substantiation && (
            <>
              <SubstantiationResults
                substantiation={substantiation}
                references={references}
                supportingFiles={supportingFiles}
              />
              {substantiation.retrievedPassages && substantiation.retrievedPassages.length > 0 && (
                <RetrievedPassagesDisplay passages={substantiation.retrievedPassages} />
              )}
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
