'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CheckCircle, AlertCircle, XCircle, ChevronDown, ChevronRight, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ClaimCommonKnowledgeResultWithClaimIndex } from '@/lib/generated-api';

export interface CommonKnowledgeAccordionProps {
  result: ClaimCommonKnowledgeResultWithClaimIndex;
  className?: string;
}

export function CommonKnowledgeAccordion({ result, className }: CommonKnowledgeAccordionProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const isCommonKnowledge = result.isCommonKnowledge ?? false;
  const needsSubstantiation = result.needsSubstantiation;
  const hasClaimTypes = result.claimTypes && result.claimTypes.length > 0;
  const hasCommonKnowledgeTypes = result.commonKnowledgeTypes && result.commonKnowledgeTypes.length > 0;
  const hasRationale = result.rationale && result.rationale.trim().length > 0;

  const hasAnyDetails = hasRationale || hasClaimTypes || hasCommonKnowledgeTypes;

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-1">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <div className={cn('p-1.5 rounded-full', isCommonKnowledge ? 'bg-blue-100' : 'bg-amber-100')}>
              {isCommonKnowledge ? (
                <CheckCircle className="h-4 w-4 text-blue-600" />
              ) : (
                <AlertCircle className="h-4 w-4 text-amber-600" />
              )}
            </div>
            Common Knowledge
          </CardTitle>
          {hasAnyDetails && (
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
        {/* Main Status - Always Visible */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">Status:</span>
            <Badge
              variant={isCommonKnowledge ? 'default' : 'secondary'}
              className={cn(
                'font-medium',
                isCommonKnowledge
                  ? 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                  : 'bg-amber-100 text-amber-800 hover:bg-amber-200',
              )}
            >
              {isCommonKnowledge ? 'Common Knowledge' : 'Not Common Knowledge'}
            </Badge>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">Needs Substantiation:</span>
            <Badge
              variant={needsSubstantiation ? 'destructive' : 'secondary'}
              className={cn(
                'font-medium',
                needsSubstantiation
                  ? 'bg-red-100 text-red-800 hover:bg-red-200'
                  : 'bg-green-100 text-green-800 hover:bg-green-200',
              )}
            >
              {needsSubstantiation ? 'Yes' : 'No'}
            </Badge>
          </div>
        </div>

        {/* Collapsible Detailed Analysis */}
        {isExpanded && hasAnyDetails && (
          <>
            <div className="border-t border-gray-200" />

            <div className="space-y-4">
              {/* Rationale */}
              {hasRationale && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Info className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium text-gray-700">Analysis Rationale:</span>
                  </div>
                  <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md leading-relaxed">{result.rationale}</p>
                </div>
              )}

              {/* Claim Types */}
              {hasClaimTypes && (
                <div className="space-y-2">
                  <span className="text-sm font-medium text-gray-700">Claim Types:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {result.claimTypes!.map((type, index) => (
                      <Badge key={index} variant="outline" className="text-xs bg-gray-50 text-gray-700 border-gray-200">
                        {type}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Common Knowledge Types */}
              {hasCommonKnowledgeTypes && (
                <div className="space-y-2">
                  <span className="text-sm font-medium text-gray-700">Common Knowledge Types:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {result.commonKnowledgeTypes!.map((type, index) => (
                      <Badge key={index} variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                        {type}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Summary */}
              <div
                className={cn(
                  'p-3 rounded-md border-l-4',
                  isCommonKnowledge ? 'bg-blue-50 border-blue-400' : 'bg-amber-50 border-amber-400',
                )}
              >
                <div className="flex items-start gap-2">
                  {isCommonKnowledge ? (
                    <CheckCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  ) : (
                    <XCircle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="text-sm">
                    <p className={cn('font-medium', isCommonKnowledge ? 'text-blue-800' : 'text-amber-800')}>
                      {isCommonKnowledge
                        ? 'This claim is considered common knowledge in the domain.'
                        : 'This claim is not considered common knowledge and may need substantiation.'}
                    </p>
                    {needsSubstantiation && (
                      <p className="text-amber-700 mt-1">
                        Even though this claim may be common knowledge, it still requires substantiation with evidence.
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
