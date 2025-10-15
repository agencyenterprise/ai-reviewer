import * as React from 'react';
import { Card, CardContent } from './card';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  children?: React.ReactNode;
}

export function EmptyState({ icon, title, description, action, children }: EmptyStateProps) {
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        {icon && <div className="mb-4 text-muted-foreground">{icon}</div>}
        <h3 className="text-lg font-semibold mb-2">{title}</h3>
        {description && <p className="text-sm text-muted-foreground mb-4 max-w-md">{description}</p>}
        {action && <div className="mt-4">{action}</div>}
        {children && <div className="mt-6 w-full">{children}</div>}
      </CardContent>
    </Card>
  );
}
