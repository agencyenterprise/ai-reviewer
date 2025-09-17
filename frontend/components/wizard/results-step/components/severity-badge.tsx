import { Badge } from '@/components/ui/badge';
import { Severity } from '@/lib/generated-api';
import { getSeverityClasses, getSeverityLabel } from '@/lib/severity';
import { cn } from '@/lib/utils';

export interface SeverityBadgeProps {
  severity: Severity;
  className?: string;
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  return (
    <Badge className={cn(getSeverityClasses(severity), 'font-normal', className)}>
      Severity: {getSeverityLabel(severity)}
    </Badge>
  );
}
