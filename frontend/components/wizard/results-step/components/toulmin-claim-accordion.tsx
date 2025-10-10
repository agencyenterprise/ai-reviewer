'use client';

import { Button } from '@/components/ui/button';
import { ToulminClaim, ToulminClaimWarrantExpressionEnum } from '@/lib/generated-api/models/ToulminClaim';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight, Info, Scale } from 'lucide-react';
import { useState } from 'react';
import { ToulminElement, ToulminElementCard } from './toulmin-elements';

export interface ToulminClaimAccordionProps {
  claim: ToulminClaim;
  className?: string;
}

export function ToulminClaimAccordion({ claim, className }: ToulminClaimAccordionProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const hasData = claim.data && claim.data.length > 0;
  const hasWarrants = claim.warrants && claim.warrants.length > 0;
  const hasQualifiers = claim.qualifiers && claim.qualifiers.length > 0;
  const hasRebuttals = claim.rebuttals && claim.rebuttals.length > 0;
  const hasBacking = claim.backing && claim.backing.length > 0;

  const warrantExpressionLabel = {
    [ToulminClaimWarrantExpressionEnum.Stated]: 'Explicitly Stated',
    [ToulminClaimWarrantExpressionEnum.Implied]: 'Implied',
    [ToulminClaimWarrantExpressionEnum.None]: 'Not Identified',
  }[claim.warrantExpression];

  const hasAnyElements =
    hasData || hasWarrants || hasQualifiers || hasRebuttals || hasBacking || claim.text || claim.rationale;

  return (
    <div className={cn('border-b pb-2 space-y-4', className)}>
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-2 font-semibold">
          <Scale className="h-4 w-4" />
          Toulmin Argument Structure
        </h3>

        {hasAnyElements && (
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
        )}
      </div>

      {isExpanded && hasAnyElements && (
        <div className="space-y-3">
          {claim.rationale && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Info className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Extraction Rationale</span>
              </div>
              <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md leading-relaxed">{claim.rationale}</p>
            </div>
          )}

          <h3 className="text-lg font-medium text-gray-900">Argument Structure</h3>
          <ToulminElementCard element={ToulminElement.DATA} items={claim.data} />
          <ToulminElementCard
            element={ToulminElement.WARRANT}
            items={claim.warrants}
            warrantExpression={warrantExpressionLabel}
          />
          <ToulminElementCard element={ToulminElement.QUALIFIER} items={claim.qualifiers} />
          <ToulminElementCard element={ToulminElement.REBUTTAL} items={claim.rebuttals} />
          <ToulminElementCard element={ToulminElement.BACKING} items={claim.backing} />
        </div>
      )}
    </div>
  );
}
