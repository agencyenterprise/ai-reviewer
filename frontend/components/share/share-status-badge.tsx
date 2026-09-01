'use client';

import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { Link } from 'lucide-react';

interface ShareStatusBadgeProps {
  isEnabled: boolean;
  onClick?: () => void;
  /**
   * Drops the label on narrow screens, leaving the link icon, the way the
   * buttons beside it in the header shed their labels.
   */
  compact?: boolean;
}

export function ShareStatusBadge({ isEnabled, onClick, compact = false }: ShareStatusBadgeProps) {
  if (!isEnabled) return null;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge
          variant="outline"
          className="h-7 cursor-pointer gap-1 bg-green-50 text-green-700 border-green-200 hover:bg-green-100 dark:bg-green-950 dark:text-green-300 dark:border-green-800 dark:hover:bg-green-900"
          onClick={onClick}
          aria-label="Sharing enabled"
        >
          <Link className="h-3 w-3" />
          <span className={cn(compact && 'hidden sm:inline')}>Sharing enabled</span>
        </Badge>
      </TooltipTrigger>
      <TooltipContent>
        <p>Click to manage share settings</p>
      </TooltipContent>
    </Tooltip>
  );
}
