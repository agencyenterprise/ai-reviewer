'use client';

import { LabeledValue } from '@/components/labeled-value';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ClaimCategorizationResponseWithClaimIndex } from '@/lib/generated-api';
import { snakeCaseToTitleCase } from '@/lib/utils';
import { ChevronDown, ChevronRight, TagIcon } from 'lucide-react';
import { useState } from 'react';

interface ClaimCategoryResultsProps {
  claimCategory: ClaimCategorizationResponseWithClaimIndex;
}

export function ClaimCategoryResults({ claimCategory }: ClaimCategoryResultsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border-b pb-2 space-y-4">
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <h3 className="flex items-center gap-2 font-semibold">
            <TagIcon className="h-4 w-4" />
            Claim Category
          </h3>

          <Button
            variant="ghost"
            size="xs"
            className="text-gray-600 hover:text-gray-900"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? (
              <>
                <ChevronDown />
                Hide Details
              </>
            ) : (
              <>
                <ChevronRight />
                Show Details
              </>
            )}
          </Button>
        </div>

        <Badge variant="outline">{snakeCaseToTitleCase(claimCategory.claimCategory)}</Badge>
      </div>

      {isExpanded && (
        <div className="space-y-2">
          <LabeledValue label="Needs External Verification">
            {claimCategory.needsExternalVerification ? 'Yes' : 'No'}
          </LabeledValue>
          <LabeledValue label="Rationale">{claimCategory.rationale}</LabeledValue>
        </div>
      )}
    </div>
  );
}
