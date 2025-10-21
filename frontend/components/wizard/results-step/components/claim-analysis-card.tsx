'use client';

import { AiGeneratedLabel } from '@/components/ai-generated-label';
import { Card, CardContent } from '@/components/ui/card';
import {
  BibliographyItem,
  CitationSuggestionResultWithClaimIndexOutput,
  ClaimCommonKnowledgeResultWithClaimIndex,
  ClaimSubstantiationResultWithClaimIndex,
  FileDocument,
  ToulminClaim,
} from '@/lib/generated-api';
import { RetrievedPassagesDisplay } from './retrieved-passages-display';
import { ClaimCitationSuggestions } from './claim-citation-suggestions';
import { ClaimNeedsSubstantiationAccordion } from './claim-needs-substantiation-accordion';
import { SubstantiationResults } from './substantiation-results';
import { ToulminClaimAccordion } from './toulmin-claim-accordion';
import { LabeledValue } from '@/components/labeled-value';

export interface ClaimAnalysisCardProps {
  claim: ToulminClaim;
  commonKnowledgeResult?: ClaimCommonKnowledgeResultWithClaimIndex;
  substantiation?: ClaimSubstantiationResultWithClaimIndex;
  references: BibliographyItem[];
  claimIndex: number;
  totalClaims: number;
  supportingFiles: FileDocument[];
  citationSuggestion?: CitationSuggestionResultWithClaimIndexOutput;
}

export function ClaimAnalysisCard({
  claim,
  commonKnowledgeResult,
  substantiation,
  references,
  supportingFiles,
  claimIndex,
  totalClaims,
  citationSuggestion,
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

        <LabeledValue label="Extracted Claim">{claim.claim}</LabeledValue>

        <div className="space-y-2">
          <ToulminClaimAccordion claim={claim} />
          {commonKnowledgeResult && <ClaimNeedsSubstantiationAccordion result={commonKnowledgeResult} />}
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
          {citationSuggestion && (
            <ClaimCitationSuggestions
              citationSuggestion={citationSuggestion}
              references={references}
              supportingFiles={supportingFiles}
            />
          )}
        </div>
      </CardContent>
    </Card>
  );
}
