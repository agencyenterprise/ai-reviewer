import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { ClaimCategory, claimCategoryTitles, claimCategoryDescriptions } from '@/lib/claim-classification';
import { cn } from '@/lib/utils';
import { AlertTriangle, CheckCircle } from 'lucide-react';

export interface ClaimCategoryLabelProps {
  category: ClaimCategory;
  badge?: boolean;
  className?: string;
}

const claimCategoryBadgeColors: Record<ClaimCategory, string> = {
  [ClaimCategory.NO_CITATION_NEEDED]: 'bg-blue-100 text-blue-800',
  [ClaimCategory.MISSING_CITATION]: 'bg-yellow-100 text-yellow-800',
  [ClaimCategory.UNVERIFIABLE_CITATION]: 'bg-yellow-100 text-yellow-800',
  [ClaimCategory.CONTRADICTORY]: 'bg-red-100 text-red-800',
  [ClaimCategory.VERIFIED]: 'bg-green-100 text-green-800',
};

const claimCategoryTextColors: Record<ClaimCategory, string> = {
  [ClaimCategory.NO_CITATION_NEEDED]: 'text-blue-600',
  [ClaimCategory.MISSING_CITATION]: 'text-yellow-600',
  [ClaimCategory.UNVERIFIABLE_CITATION]: 'text-yellow-600',
  [ClaimCategory.CONTRADICTORY]: 'text-red-600',
  [ClaimCategory.VERIFIED]: 'text-green-600',
};

const claimCategoryIcons: Record<ClaimCategory, React.ReactNode> = {
  [ClaimCategory.NO_CITATION_NEEDED]: <CheckCircle className="w-3 h-3" />,
  [ClaimCategory.MISSING_CITATION]: <AlertTriangle className="w-3 h-3" />,
  [ClaimCategory.UNVERIFIABLE_CITATION]: <AlertTriangle className="w-3 h-3" />,
  [ClaimCategory.CONTRADICTORY]: <AlertTriangle className="w-3 h-3" />,
  [ClaimCategory.VERIFIED]: <CheckCircle className="w-3 h-3" />,
};

export function ClaimCategoryLabel({ category, className, badge = true }: ClaimCategoryLabelProps) {
  return (
    <Tooltip>
      <TooltipTrigger>
        <span
          className={cn(
            'text-xs flex items-center gap-1',
            badge ? claimCategoryBadgeColors[category] : claimCategoryTextColors[category],
            badge ? 'px-2 py-1 rounded' : '',
            className,
          )}
        >
          {claimCategoryIcons[category]}
          {claimCategoryTitles[category]}
        </span>
      </TooltipTrigger>
      <TooltipContent>{claimCategoryDescriptions[category]}</TooltipContent>
    </Tooltip>
  );
}
