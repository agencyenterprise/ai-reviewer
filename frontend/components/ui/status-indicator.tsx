import React from 'react';
import { Badge } from './badge';
import { WorkflowRunStatus } from '@/lib/generated-api';
import { AlertTriangle, Check, Clock, Loader2 } from 'lucide-react';

interface StatusIndicatorProps {
  status: WorkflowRunStatus;
  className?: string;
}

export function StatusIndicator({ status, className }: StatusIndicatorProps) {
  const getStatusConfig = (status: WorkflowRunStatus) => {
    switch (status) {
      case 'pending':
        return {
          label: 'Pending',
          variant: 'secondary' as const,
          icon: <Clock className="h-3 w-3" />,
        };
      case 'running':
        return {
          label: 'Running',
          variant: 'default' as const,
          icon: <Loader2 className="h-3 w-3 animate-spin" />,
        };
      case 'completed':
        return {
          label: 'Completed',
          variant: 'outline' as const,
          icon: <Check className="h-3 w-3" />,
        };
      default:
        return {
          label: 'Unknown',
          variant: 'secondary' as const,
          icon: <AlertTriangle className="h-3 w-3" />,
        };
    }
  };

  const config = getStatusConfig(status);

  return (
    <Badge variant={config.variant} className={className}>
      {config.icon}
      {config.label}
    </Badge>
  );
}
