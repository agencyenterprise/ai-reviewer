import * as React from 'react';
import { Loader2 } from 'lucide-react';
import { EmptyState } from '@/components/ui/empty-state';
import { SkeletonList, SkeletonParagraphs } from '@/components/ui/skeleton-list';

interface TabWithLoadingStatesProps<T> {
  title: string;
  data: T | undefined;
  isProcessing: boolean;
  hasData: (data: T | undefined) => boolean;
  loadingMessage: { title: string; description: string };
  emptyMessage: { icon: React.ReactNode; title: string; description?: string };
  emptyStateChildren?: React.ReactNode;
  skeletonType?: 'list' | 'paragraphs';
  skeletonCount?: number;
  children: (data: T) => React.ReactNode;
}

/**
 * Higher-order component that provides consistent loading and empty states for tab content.
 * Handles three states:
 * 1. Loading: Shows spinner, message, and skeleton placeholders
 * 2. Empty: Shows icon and explanation message
 * 3. Data: Renders children with actual data
 */
export function TabWithLoadingStates<T>({
  title,
  data,
  isProcessing,
  hasData,
  loadingMessage,
  emptyMessage,
  emptyStateChildren,
  skeletonType = 'list',
  skeletonCount = 3,
  children,
}: TabWithLoadingStatesProps<T>) {
  const isLoading = !hasData(data) && isProcessing;

  if (isLoading) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        <EmptyState
          icon={<Loader2 className="h-12 w-12 animate-spin text-primary" />}
          title={loadingMessage.title}
          description={loadingMessage.description}
        >
          {skeletonType === 'list' ? (
            <SkeletonList count={skeletonCount} />
          ) : (
            <SkeletonParagraphs count={skeletonCount} />
          )}
        </EmptyState>
      </div>
    );
  }

  if (!hasData(data)) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        <EmptyState {...emptyMessage}>{emptyStateChildren}</EmptyState>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">{title}</h3>
      {children(data!)}
    </div>
  );
}
