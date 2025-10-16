'use client';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { ClaimCommonKnowledgeResultWithClaimIndex } from '@/lib/generated-api';
import { cn } from '@/lib/utils';
import { AlertCircle, CheckCircle, ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';

export interface CommonKnowledgeAccordionProps {
  result: ClaimCommonKnowledgeResultWithClaimIndex;
  className?: string;
}

export function CommonKnowledgeAccordion({ result, className }: CommonKnowledgeAccordionProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const isCommonKnowledge = result.isCommonKnowledge ?? false;
  const needsSubstantiation = result.needsSubstantiation;

  return (
    <div className={cn('border-b pb-2 space-y-4', className)}>
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <h3 className="flex items-center gap-2 font-semibold">
            {isCommonKnowledge ? <CheckCircle className="h-4 w-4 " /> : <AlertCircle className="h-4 w-4" />}
            Common Knowledge Check
          </h3>

          <Button
            variant="ghost"
            size="xs"
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-600 hover:text-gray-900"
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
        <div className="flex items-center gap-1">
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge
                variant={isCommonKnowledge ? 'default' : 'secondary'}
                className={cn(
                  'font-medium cursor-help',
                  isCommonKnowledge
                    ? 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                    : 'bg-amber-100 text-amber-800 hover:bg-amber-200',
                )}
              >
                {isCommonKnowledge ? 'Common Knowledge' : 'Not Common Knowledge'}
              </Badge>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-sm">
              <p className="text-xs leading-relaxed">{result.commonKnowledgeRationale}</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Badge
                variant={needsSubstantiation ? 'destructive' : 'secondary'}
                className={cn(
                  'font-medium cursor-help',
                  needsSubstantiation
                    ? 'bg-red-100 text-red-800 hover:bg-red-200'
                    : 'bg-green-100 text-green-800 hover:bg-green-200',
                )}
              >
                {needsSubstantiation ? 'Needs Substantiation' : 'No Substantiation Needed'}
              </Badge>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-sm">
              <p className="text-xs leading-relaxed">{result.substantiationRationale}</p>
            </TooltipContent>
          </Tooltip>
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-2">
          <p className="text-sm leading-relaxed">
            <span className="font-medium">Needs Substantiation:</span> {result.needsSubstantiation ? 'Yes' : 'No'}
          </p>
          <p className="text-sm leading-relaxed">
            <span className="font-medium">Substantiation Rationale:</span> {result.substantiationRationale}
          </p>
          <p className="text-sm leading-relaxed">
            <span className="font-medium">Is Common Knowledge:</span> {result.isCommonKnowledge ? 'Yes' : 'No'}
          </p>
          <p className="text-sm leading-relaxed">
            <span className="font-medium">Common Knowledge Rationale:</span> {result.commonKnowledgeRationale}
          </p>
          {result.claimTypes && result.claimTypes.length > 0 && (
            <p className="text-sm leading-relaxed">
              <span className="font-medium">Claim Types:</span> {result.claimTypes?.join(', ')}
            </p>
          )}
          {result.commonKnowledgeTypes && result.commonKnowledgeTypes.length > 0 && (
            <p className="text-sm leading-relaxed">
              <span className="font-medium">Common Knowledge Types:</span> {result.commonKnowledgeTypes?.join(', ')}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
