'use client';

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useExperimentalFeatures } from '@/context/experimental-features-context';
import { RAIL_ITEM_ACTIVE } from '@/lib/rail-style';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import { HELP_TOPICS, HelpTopicId } from './topics';

interface HelpCenterProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** The topic the link that opened this promised. */
  topic: HelpTopicId;
  /** Forwarded to the topic that has somewhere to send the reader. */
  onReviewReferences?: () => void;
}

/**
 * One dialog for every concept the app has to explain, with the list of them
 * down the side. A reader who arrives asking about source files can see that
 * revisions are also explained, which a one-off modal per question never shows
 * them.
 */
export function HelpCenter({ open, onOpenChange, topic, onReviewReferences }: HelpCenterProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/* Wide enough that the navigation costs the content nothing: the traces
          in a topic are three columns of prose that stack the moment they are
          squeezed. */}
      <DialogContent className="gap-0 p-0 sm:max-w-5xl">
        {/* Keyed on the topic, and unmounted between openings: either way the
            dialog starts on the topic of the link that was clicked, rather than
            wherever the last reader wandered off to. */}
        <HelpCenterBody key={topic} initialTopic={topic} onReviewReferences={onReviewReferences} />
      </DialogContent>
    </Dialog>
  );
}

function HelpCenterBody({
  initialTopic,
  onReviewReferences,
}: {
  initialTopic: HelpTopicId;
  onReviewReferences?: () => void;
}) {
  const [topicId, setTopicId] = useState<HelpTopicId>(initialTopic);
  const { showExperimentalFeatures } = useExperimentalFeatures();
  const topics = HELP_TOPICS.filter((entry) => showExperimentalFeatures || !entry.experimental);
  const topic = topics.find((entry) => entry.id === topicId) ?? topics[0];
  const { Body } = topic;

  return (
    <div className="flex max-h-[80vh] min-h-0 flex-col sm:flex-row">
      {/* A column beside the content, and a strip above it where there is no
          room for one. */}
      <nav
        aria-label="Help topics"
        className="flex shrink-0 gap-1 overflow-x-auto border-b p-2 sm:w-52 sm:flex-col sm:overflow-visible sm:border-r sm:border-b-0 sm:p-3"
      >
        <p className="hidden px-2 pb-1 font-mono text-[10px] tracking-wide text-muted-foreground uppercase sm:block">
          Help
        </p>
        {topics.map((entry) => (
          <button
            key={entry.id}
            onClick={() => setTopicId(entry.id)}
            aria-current={entry.id === topicId ? 'page' : undefined}
            className={cn(
              'flex shrink-0 cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors',
              entry.id === topicId
                ? RAIL_ITEM_ACTIVE
                : 'text-muted-foreground hover:bg-accent/60 hover:text-foreground',
            )}
          >
            <entry.icon className="size-3.5 shrink-0" aria-hidden />
            {entry.label}
          </button>
        ))}
      </nav>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        {/* pr-12 keeps the heading clear of the dialog's own close button. */}
        <DialogHeader className="shrink-0 border-b p-4 pr-12 text-left">
          <DialogTitle className="text-base">{topic.title}</DialogTitle>
          <DialogDescription>{topic.description}</DialogDescription>
        </DialogHeader>

        <div className="min-h-0 flex-1 overflow-y-auto p-4 text-sm">
          <Body onReviewReferences={onReviewReferences} onOpenTopic={setTopicId} />
        </div>
      </div>
    </div>
  );
}
