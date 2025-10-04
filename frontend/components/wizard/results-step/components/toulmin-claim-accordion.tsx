'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Scale, ChevronDown, ChevronRight, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ToulminClaim, ToulminClaimWarrantExpressionEnum } from '@/lib/generated-api/models/ToulminClaim';
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
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-1">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <div className="p-1.5 rounded-full bg-indigo-100">
              <Scale className="h-4 w-4 text-indigo-600" />
            </div>
            Claim
          </CardTitle>
          {hasAnyElements && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
            >
              {isExpanded ? (
                <>
                  <ChevronDown className="h-4 w-4" />
                  Hide Details
                </>
              ) : (
                <>
                  <ChevronRight className="h-4 w-4" />
                  Show Details
                </>
              )}
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Main Claim - Always Visible */}
        <div className="bg-gray-50 p-4 rounded-md border-l-4 border-gray-400">
          <p className="text-gray-800 font-medium leading-relaxed">{claim.claim}</p>
        </div>

        {/* Collapsible Detailed Analysis */}
        {isExpanded && hasAnyElements && (
          <>
            <div className="border-t border-gray-200" />

            <div className="space-y-4">
              {/* Related Text */}
              {claim.text && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Related Text</h4>
                  <div className="bg-gray-50 p-4 rounded-md border-l-4 border-gray-400">
                    <p className="text-gray-800 font-medium leading-relaxed">{claim.text}</p>
                  </div>
                </div>
              )}

              {/* Extraction Rationale */}
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

              {/* Data/Grounds */}
              <ToulminElementCard element={ToulminElement.DATA} items={claim.data} />

              {/* Warrants */}
              <ToulminElementCard
                element={ToulminElement.WARRANT}
                items={claim.warrants}
                warrantExpression={warrantExpressionLabel}
              />

              {/* Qualifiers */}
              <ToulminElementCard element={ToulminElement.QUALIFIER} items={claim.qualifiers} />

              {/* Rebuttals */}
              <ToulminElementCard element={ToulminElement.REBUTTAL} items={claim.rebuttals} />

              {/* Backing */}
              <ToulminElementCard element={ToulminElement.BACKING} items={claim.backing} />
            </div>

            {/* Summary */}
            <div className="bg-indigo-50 p-4 rounded-md border-l-4 border-indigo-400">
              <div className="flex items-start gap-2">
                <Scale className="h-4 w-4 text-indigo-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm">
                  <p className="font-medium text-indigo-800 mb-2">Toulmin Argument Structure Summary</p>
                  <div className="space-y-1 text-indigo-700">
                    <p>
                      • <strong>Claim:</strong> {claim.claim}
                    </p>
                    {hasData && (
                      <p>
                        • <strong>Evidence:</strong> {claim.data!.length} data point(s) provided
                      </p>
                    )}
                    {hasWarrants && (
                      <p>
                        • <strong>Reasoning:</strong> {claim.warrants!.length} warrant(s) identified (
                        {warrantExpressionLabel.toLowerCase()})
                      </p>
                    )}
                    {hasQualifiers && (
                      <p>
                        • <strong>Scope:</strong> {claim.qualifiers!.length} qualifier(s) limiting the claim
                      </p>
                    )}
                    {hasRebuttals && (
                      <p>
                        • <strong>Counter-arguments:</strong> {claim.rebuttals!.length} rebuttal(s) acknowledged
                      </p>
                    )}
                    {hasBacking && (
                      <p>
                        • <strong>Support:</strong> {claim.backing!.length} backing element(s) provided
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
