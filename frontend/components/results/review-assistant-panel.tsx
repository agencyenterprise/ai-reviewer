'use client';

import { useProjectView } from '@/components/results/project-view-context';
import { useExperimentalFeatures } from '@/context/experimental-features-context';
import { ReviewAssistantTab } from './review-assistant/review-assistant-tab';

/** The Review Assistant tab as a tab panel, taking its project from the shell. */
export function ReviewAssistantPanel() {
  const { overview, readOnly } = useProjectView();
  // Alpha: the tab, and the route behind it, exist only for
  // users who opted in.
  const { showExperimentalFeatures, isLoading } = useExperimentalFeatures();

  if (isLoading) return null;

  if (!showExperimentalFeatures) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <p className="max-w-sm text-center text-sm leading-relaxed text-muted-foreground">
          Review Assistant is an alpha feature. Turn on <strong className="font-medium">Alpha features</strong> in your
          profile menu to use it.
        </p>
      </div>
    );
  }

  return <ReviewAssistantTab overview={overview} readOnly={readOnly} />;
}
