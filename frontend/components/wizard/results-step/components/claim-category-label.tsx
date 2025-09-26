import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { ClaimCategory, claimCategoryTitles, claimCategoryDescriptions } from '@/lib/claim-classification';
import { cn } from '@/lib/utils';
import { AlertTriangle, CheckCircle, Info } from 'lucide-react';

export interface ClaimCategoryLabelProps {
  category: ClaimCategory;
  badge?: boolean;
  className?: string;
}

const claimCategoryBadgeColors: Record<ClaimCategory, string> = {
  [ClaimCategory.NO_CITATION_NEEDED]: 'bg-blue-100 text-blue-800',
  [ClaimCategory.MISSING_CITATION]: 'bg-yellow-100 text-yellow-800',
  [ClaimCategory.PROBABLY_COMMON_KNOWLEDGE]: 'bg-amber-100 text-amber-800',
  [ClaimCategory.UNVERIFIABLE_CITATION]: 'bg-yellow-100 text-yellow-800',
  [ClaimCategory.CONTRADICTORY]: 'bg-red-100 text-red-800',
  [ClaimCategory.VERIFIED]: 'bg-green-100 text-green-800',
};

const claimCategoryTextColors: Record<ClaimCategory, string> = {
  [ClaimCategory.NO_CITATION_NEEDED]: 'text-blue-600',
  [ClaimCategory.MISSING_CITATION]: 'text-yellow-600',
  [ClaimCategory.PROBABLY_COMMON_KNOWLEDGE]: 'text-amber-600',
  [ClaimCategory.UNVERIFIABLE_CITATION]: 'text-yellow-600',
  [ClaimCategory.CONTRADICTORY]: 'text-red-600',
  [ClaimCategory.VERIFIED]: 'text-green-600',
};

const claimCategoryIcons: Record<ClaimCategory, React.ReactNode> = {
  [ClaimCategory.NO_CITATION_NEEDED]: <CheckCircle />,
  [ClaimCategory.MISSING_CITATION]: <AlertTriangle />,
  [ClaimCategory.PROBABLY_COMMON_KNOWLEDGE]: <Info />,
  [ClaimCategory.UNVERIFIABLE_CITATION]: <AlertTriangle />,
  [ClaimCategory.CONTRADICTORY]: <AlertTriangle />,
  [ClaimCategory.VERIFIED]: <CheckCircle />,
};

export function ClaimCategoryLabel({ category, className, badge = true }: ClaimCategoryLabelProps) {
  return (
    <Tooltip>
      <TooltipTrigger>
        <Badge
          className={cn(
            badge ? claimCategoryBadgeColors[category] : claimCategoryTextColors[category],
            !badge && 'bg-transparent p-0',
            'font-normal',
            className,
          )}
        >
          {claimCategoryIcons[category]} {claimCategoryTitles[category]}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>{claimCategoryDescriptions[category]}</TooltipContent>
    </Tooltip>
  );
}
