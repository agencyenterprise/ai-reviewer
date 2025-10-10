import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { EvidenceAlignmentLevel } from '@/lib/generated-api';
import { cn } from '@/lib/utils';
import { AlertTriangle, CheckCircle } from 'lucide-react';

export interface EvidenceAlignmentLevelBadgeProps {
  evidenceAlignment: EvidenceAlignmentLevel;
  badge?: boolean;
  className?: string;
  count?: number;
}

const colors: Record<EvidenceAlignmentLevel, string> = {
  [EvidenceAlignmentLevel.Supported]: 'bg-green-100 text-green-800',
  [EvidenceAlignmentLevel.PartiallySupported]: 'bg-yellow-100 text-yellow-800',
  [EvidenceAlignmentLevel.Unverifiable]: 'bg-gray-100 text-gray-800',
  [EvidenceAlignmentLevel.Contradicted]: 'bg-red-100 text-red-800',
  [EvidenceAlignmentLevel.Unsupported]: 'bg-red-100 text-red-800',
};

const textColors: Record<EvidenceAlignmentLevel, string> = {
  [EvidenceAlignmentLevel.Supported]: 'text-green-600',
  [EvidenceAlignmentLevel.PartiallySupported]: 'text-yellow-600',
  [EvidenceAlignmentLevel.Unverifiable]: 'text-gray-600',
  [EvidenceAlignmentLevel.Contradicted]: 'text-red-600',
  [EvidenceAlignmentLevel.Unsupported]: 'text-red-600',
};

const icons: Record<EvidenceAlignmentLevel, React.ReactNode> = {
  [EvidenceAlignmentLevel.Supported]: <CheckCircle />,
  [EvidenceAlignmentLevel.PartiallySupported]: <AlertTriangle />,
  [EvidenceAlignmentLevel.Unverifiable]: <AlertTriangle />,
  [EvidenceAlignmentLevel.Contradicted]: <AlertTriangle />,
  [EvidenceAlignmentLevel.Unsupported]: <AlertTriangle />,
};

const titles: Record<EvidenceAlignmentLevel, string> = {
  [EvidenceAlignmentLevel.Supported]: 'Supported',
  [EvidenceAlignmentLevel.PartiallySupported]: 'Partially supported',
  [EvidenceAlignmentLevel.Unverifiable]: 'Unverifiable',
  [EvidenceAlignmentLevel.Contradicted]: 'Contradicted',
  [EvidenceAlignmentLevel.Unsupported]: 'Unsupported',
};

const descriptions: Record<EvidenceAlignmentLevel, string> = {
  [EvidenceAlignmentLevel.Supported]: 'The supporting document(s) directly provide evidence for the claim.',
  [EvidenceAlignmentLevel.PartiallySupported]:
    'The supporting document(s) provide related evidence but do not fully substantiate the claim.',
  [EvidenceAlignmentLevel.Unverifiable]:
    'The supporting document(s) were not provided, or are inaccessible to confirm or deny the claim.',
  [EvidenceAlignmentLevel.Contradicted]: 'The supporting document(s) actually disagree with the claim.',
  [EvidenceAlignmentLevel.Unsupported]: 'The supporting document(s) do not provide evidence for the claim.',
};

export function EvidenceAlignmentLevelBadge({
  evidenceAlignment,
  className,
  badge = true,
  count,
}: EvidenceAlignmentLevelBadgeProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge
          className={cn(
            badge ? colors[evidenceAlignment] : textColors[evidenceAlignment],
            !badge && 'bg-transparent p-0',
            className,
          )}
        >
          {count && (
            <>
              {icons[evidenceAlignment]} {count} {titles[evidenceAlignment]} claim{count > 1 ? 's' : ''}
            </>
          )}
          {!count && (
            <>
              {icons[evidenceAlignment]} {titles[evidenceAlignment]}
            </>
          )}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>{descriptions[evidenceAlignment]}</TooltipContent>
    </Tooltip>
  );
}
