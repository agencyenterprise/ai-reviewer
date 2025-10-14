import * as React from 'react';
import { Card } from './card';

interface SkeletonListProps {
  count?: number;
  className?: string;
}

export function SkeletonList({ count = 3, className = '' }: SkeletonListProps) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: count }).map((_, index) => (
        <Card key={index} className="p-4 animate-pulse">
          <div className="space-y-3">
            <div className="h-4 bg-muted rounded w-3/4"></div>
            <div className="h-3 bg-muted rounded w-full"></div>
            <div className="h-3 bg-muted rounded w-5/6"></div>
          </div>
        </Card>
      ))}
    </div>
  );
}

interface SkeletonParagraphsProps {
  count?: number;
  className?: string;
}

export function SkeletonParagraphs({ count = 4, className = '' }: SkeletonParagraphsProps) {
  return (
    <div className={`space-y-4 ${className}`}>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="space-y-2 animate-pulse">
          <div className="h-3 bg-muted rounded w-full"></div>
          <div className="h-3 bg-muted rounded w-full"></div>
          <div className="h-3 bg-muted rounded w-4/5"></div>
        </div>
      ))}
    </div>
  );
}
