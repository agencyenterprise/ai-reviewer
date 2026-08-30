'use client';

import { cn } from '@/lib/utils';
import { ReactNode, useState } from 'react';
import { HelpCenter } from './help-center';
import { HelpTopicId } from './topics';

interface HelpLinkProps {
  topic: HelpTopicId;
  /** The link's words. Default asks the question the reader is already asking. */
  children?: ReactNode;
  className?: string;
  /** Forwarded to the source-files topic, where it has somewhere to send them. */
  onReviewReferences?: () => void;
}

/**
 * A quiet link that opens the help centre on one topic, with the dialog it
 * needs. One component so that adding an explanation somewhere is a single
 * line, and so every one of them looks and behaves the same.
 */
export function HelpLink({ topic, children = 'What is this?', className, onReviewReferences }: HelpLinkProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={(event) => {
          // These sit inside labels, rows and cards that act on a click of
          // their own; asking what something is must not also choose it.
          event.preventDefault();
          event.stopPropagation();
          setOpen(true);
        }}
        className={cn(
          'cursor-pointer underline underline-offset-2 text-muted-foreground hover:text-foreground',
          className,
        )}
      >
        {children}
      </button>

      <HelpCenter
        open={open}
        onOpenChange={setOpen}
        topic={topic}
        onReviewReferences={
          onReviewReferences &&
          (() => {
            setOpen(false);
            onReviewReferences();
          })
        }
      />
    </>
  );
}
