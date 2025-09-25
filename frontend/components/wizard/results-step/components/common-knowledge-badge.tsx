import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ClaimCategory } from '@/lib/claim-classification';

export interface CommonKnowledgeBadgeProps {
  isCommonKnowledge: boolean;
  commonKnowledgeRationale?: string;
  claimCategory?: ClaimCategory;
  className?: string;
}

export function CommonKnowledgeBadge({
  isCommonKnowledge,
  commonKnowledgeRationale,
  claimCategory,
  className,
}: CommonKnowledgeBadgeProps) {
  if (!isCommonKnowledge) {
    return null;
  }

  // Don't show the badge if the claim category is already "Probably Common Knowledge"
  // since the ClaimCategoryLabel will already show that information
  if (claimCategory === ClaimCategory.PROBABLY_COMMON_KNOWLEDGE) {
    return null;
  }

  // For other cases, show the regular Common Knowledge badge
  return (
    <div className="inline-flex items-center gap-1">
      <Badge variant="secondary" className={cn('bg-blue-100 text-blue-800 font-normal', className)}>
        Common Knowledge
      </Badge>
      <Tooltip>
        <TooltipTrigger asChild>
          <Info className="h-3 w-3 text-blue-600 hover:text-blue-800 cursor-help" />
        </TooltipTrigger>
        <TooltipContent className="max-w-md">
          <div className="space-y-1.5">
            <p className="font-medium text-sm">Common Knowledge</p>
            <p className="text-xs text-gray-200">Facts that don&apos;t need citation:</p>
            <ul className="text-xs space-y-0.5 ml-2">
              <li>• Well-established facts in the domain</li>
              <li>• Basic definitions and terminology</li>
              <li>• Logical deductions from stated premises</li>
              <li>• General principles universally accepted</li>
            </ul>
            {commonKnowledgeRationale && (
              <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                <p className="font-medium text-gray-700 mb-1">AI Assessment:</p>
                <p className="text-gray-600">{commonKnowledgeRationale}</p>
              </div>
            )}
            <p className="text-xs text-gray-300 mt-1.5">Domain experts wouldn&apos;t question these claims.</p>
          </div>
        </TooltipContent>
      </Tooltip>
    </div>
  );
}
