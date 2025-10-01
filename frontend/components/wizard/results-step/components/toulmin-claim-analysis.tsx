import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle, AlertTriangle, Quote, Shield, Scale, Zap, RotateCcw, Layers, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ToulminClaim, ToulminClaimWarrantExpressionEnum } from '@/lib/generated-api/models/ToulminClaim';

export interface ToulminClaimAnalysisProps {
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
    <div className="space-y-3">
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
          <Badge
            variant="outline"
            className={cn('text-xs', element.color === 'purple' && 'bg-purple-50 text-purple-700 border-purple-200')}
          >
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

export function ToulminClaimAnalysis({ claim, className }: ToulminClaimAnalysisProps) {
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

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-1">
        <CardTitle className="flex items-center gap-2 text-lg">
          <div className="p-1.5 rounded-full bg-indigo-100">
            <Scale className="h-4 w-4 text-indigo-600" />
          </div>
          Claim Information
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Main Claim */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-gray-900">Main Claim</h3>
          </div>

          <div className="bg-gray-50 p-4 rounded-md border-l-4 border-gray-400">
            <p className="text-gray-800 font-medium leading-relaxed">{claim.claim}</p>
          </div>

          <h3 className="font-medium text-gray-900">Related text:</h3>
          <div className="bg-gray-50 p-4 rounded-md border-l-4 border-gray-400">
            <p className="text-gray-800 font-medium leading-relaxed">{claim.text}</p>
          </div>

          {claim.rationale && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Info className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Extraction Rationale:</span>
              </div>
              <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md leading-relaxed">{claim.rationale}</p>
            </div>
          )}
        </div>

        <div className="border-t border-gray-200" />

        {/* Toulmin Elements */}
        <div className="space-y-6">
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
                <p>
                  • <strong>Substantiation Required:</strong> {claim.needsSubstantiation ? 'Yes' : 'No'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
