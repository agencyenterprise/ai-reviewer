'use client';

import { Button } from '@/components/ui/button';
import { ClaimSubstantiationResultWithClaimIndex } from '@/lib/generated-api';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight, FileSearch } from 'lucide-react';
import { useState } from 'react';
import { EvidenceAlignmentLevelBadge } from './evidence-alignment-level-badge';

interface SubstantiationResultsProps {
  substantiation: ClaimSubstantiationResultWithClaimIndex;
  className?: string;
}

export function SubstantiationResults({ substantiation, className = '' }: SubstantiationResultsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className={cn('border-b pb-2 space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="flex items-center gap-2 font-semibold">
            <FileSearch className="h-4 w-4" />
            Claim-Reference Validation
          </h3>

          <EvidenceAlignmentLevelBadge evidenceAlignment={substantiation.evidenceAlignment} badge={true} />
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
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

      {isExpanded && (
        <div className="space-y-2">
          <p className="text-sm leading-relaxed">
            <span className="font-medium">Evidence Alignment:</span> {substantiation.evidenceAlignment}
          </p>
          <p className="text-sm leading-relaxed">
            <span className="font-medium">Rationale:</span> {substantiation.rationale}
          </p>
          <p className="text-sm leading-relaxed">
            <span className="font-medium">Feedback to resolve:</span> {substantiation.feedback}
          </p>
        </div>
      )}
    </div>
  );
}
