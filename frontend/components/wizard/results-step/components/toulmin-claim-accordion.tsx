'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Scale, ChevronDown, ChevronRight, Quote, Shield, RotateCcw, Layers, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ToulminClaim, ToulminClaimWarrantExpressionEnum } from '@/lib/generated-api/models/ToulminClaim';

export interface ToulminClaimAccordionProps {
  claim: ToulminClaim;
  className?: string;
}

const ToulminElement = {
  DATA: { icon: Quote, color: 'blue', label: 'Data/Grounds' },
  WARRANT: { icon: Shield, color: 'purple', label: 'Warrants' },
  QUALIFIER: { icon: Scale, color: 'green', label: 'Qualifiers' },
  REBUTTAL: { icon: RotateCcw, color: 'orange', label: 'Rebuttals' },
  BACKING: { icon: Layers, color: 'indigo', label: 'Backing' },
} as const;

function ToulminElementCard({
  element,
  items,
  warrantExpression,
}: {
  element: (typeof ToulminElement)[keyof typeof ToulminElement];
  items?: string[];
  warrantExpression?: string;
}) {
  const Icon = element.icon;

  if (!items || items.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <div
          className={cn(
            'p-1.5 rounded-full',
            element.color === 'blue' && 'bg-blue-100',
            element.color === 'purple' && 'bg-purple-100',
            element.color === 'green' && 'bg-green-100',
            element.color === 'orange' && 'bg-orange-100',
            element.color === 'indigo' && 'bg-indigo-100',
          )}
        >
          <Icon
            className={cn(
              'h-4 w-4',
              element.color === 'blue' && 'text-blue-600',
              element.color === 'purple' && 'text-purple-600',
              element.color === 'green' && 'text-green-600',
              element.color === 'orange' && 'text-orange-600',
              element.color === 'indigo' && 'text-indigo-600',
            )}
          />
        </div>
        <h4 className="font-medium text-gray-900">{element.label}</h4>
        {warrantExpression && (
          <Badge variant="outline" className="text-xs">
            {warrantExpression}
          </Badge>
        )}
      </div>

      <div className="space-y-2">
        {items.map((item, index) => (
          <div
            key={index}
            className={cn(
              'p-3 rounded-md text-sm',
              element.color === 'blue' && 'bg-blue-50 border-l-4 border-blue-400',
              element.color === 'purple' && 'bg-purple-50 border-l-4 border-purple-400',
              element.color === 'green' && 'bg-green-50 border-l-4 border-green-400',
              element.color === 'orange' && 'bg-orange-50 border-l-4 border-orange-400',
              element.color === 'indigo' && 'bg-indigo-50 border-l-4 border-indigo-400',
            )}
          >
            <p className="text-gray-700 leading-relaxed">{item}</p>
          </div>
        ))}
      </div>
    </div>
  );
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
