import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Info } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface CommonKnowledgeBadgeProps {
  isCommonKnowledge: boolean;
  className?: string;
}

export function CommonKnowledgeBadge({ isCommonKnowledge, className }: CommonKnowledgeBadgeProps) {
  if (!isCommonKnowledge) {
    return null;
  }

  return (
    <div className="inline-flex items-center gap-1">
      <Badge variant="secondary" className={cn('bg-blue-100 text-blue-800 font-normal', className)}>
        Common Knowledge
      </Badge>
      <Tooltip>
        <TooltipTrigger asChild>
          <Info className="h-3 w-3 text-blue-600 hover:text-blue-800 cursor-help" />
        </TooltipTrigger>
        <TooltipContent className="max-w-xs">
          <div className="space-y-1.5">
            <p className="font-medium text-sm">Common Knowledge</p>
            <p className="text-xs text-gray-200">Facts that don&apos;t need citation:</p>
            <ul className="text-xs space-y-0.5 ml-2">
              <li>• Well-established facts in the domain</li>
              <li>• Basic definitions and terminology</li>
              <li>• Logical deductions from stated premises</li>
              <li>• General principles universally accepted</li>
            </ul>
            <p className="text-xs text-gray-300 mt-1.5">Domain experts wouldn&apos;t question these claims.</p>
          </div>
        </TooltipContent>
      </Tooltip>
    </div>
  );
}
