'use client';

import { Button } from '@/components/ui/button';
import { ThreadPrimitive } from '@assistant-ui/react';
import type { FC } from 'react';

// One per thing the pane does that a plain chat can't: tracked changes, comments, and
// reading the document's figures.
const STARTERS = [
  'Tighten the selected paragraph and suggest the edits as tracked changes.',
  'Add comments where a claim needs a source or more evidence.',
  'Do the figures match what the text says about them?',
];

/**
 * The `Welcome` slot of assistant-ui's Thread in the Word pane, after /chat's
 * (`components/chat/chat-welcome.tsx`). The document is already open, so a starter
 * sends at once rather than waiting for an attachment.
 */
export const PaneWelcome: FC = () => (
  <div className="aui-thread-welcome-root mb-6 flex flex-col gap-4 px-2">
    <div>
      <h1 className="fade-in slide-in-from-bottom-1 animate-in fill-mode-both font-semibold text-base duration-200">
        Ask Draft Detective about this document.
      </h1>
      <p className="fade-in slide-in-from-bottom-1 animate-in fill-mode-both text-muted-foreground text-sm delay-75 duration-200">
        It reads the document as it is now, and can suggest comments and tracked changes for you to apply.
      </p>
    </div>
    <div className="grid w-full gap-2">
      {STARTERS.map((prompt) => (
        <ThreadPrimitive.Suggestion key={prompt} prompt={prompt} send asChild>
          <Button
            variant="ghost"
            className="fade-in slide-in-from-bottom-2 animate-in fill-mode-both h-auto w-full justify-start whitespace-normal rounded-xl border px-3 py-2 text-left text-sm duration-200 hover:bg-muted"
          >
            {prompt}
          </Button>
        </ThreadPrimitive.Suggestion>
      ))}
    </div>
  </div>
);
