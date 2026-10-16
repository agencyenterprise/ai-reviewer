'use client';

import { Button } from '@/components/ui/button';
import { ThreadPrimitive } from '@assistant-ui/react';
import type { FC } from 'react';

// Draft Detective starter prompts shown on the empty thread. Clicking one
// pre-fills the composer (send=false) so the user can attach their document
// (or tweak the wording) before sending; skills prompt for an upload if none
// is attached.
const WELCOME_SUGGESTIONS: { label: string; prompt: string }[] = [
  { label: 'What checks can you run?', prompt: 'What checks can you run on my document?' },
  {
    label: 'Validate the document’s references',
    prompt: 'Validate the references in my document against their real published sources.',
  },
  {
    label: 'Peer-review my draft as “Reviewer 2”',
    prompt: 'Act as Reviewer 2 and give a rigorous peer review of my document.',
  },
  {
    label: 'Check my claims against their citations',
    prompt: 'Check whether the claims in my document are supported by their cited sources.',
  },
];

/** The `Welcome` slot of assistant-ui's Thread: our greeting and starter prompts. */
export const ChatWelcome: FC = () => (
  <div className="aui-thread-welcome-root mb-6 flex flex-col gap-4 px-2">
    <div>
      <h1 className="fade-in slide-in-from-bottom-1 animate-in fill-mode-both font-semibold text-2xl duration-200">
        Draft Detective, on the case.
      </h1>
      <p className="fade-in slide-in-from-bottom-1 animate-in fill-mode-both text-muted-foreground text-lg delay-75 duration-200">
        Your peer review assistant. Paste or upload a draft (or just a section), then ask me to check its claims,
        citations, methodology, structure, and more.
      </p>
    </div>
    <div className="grid w-full @md:grid-cols-2 gap-2">
      {WELCOME_SUGGESTIONS.map((suggestion) => (
        <ThreadPrimitive.Suggestion key={suggestion.label} prompt={suggestion.prompt} send={false} asChild>
          <Button
            variant="ghost"
            className="fade-in slide-in-from-bottom-2 animate-in fill-mode-both h-auto w-full justify-start rounded-xl border px-4 py-3 text-left text-sm duration-200 hover:bg-muted"
          >
            {suggestion.label}
          </Button>
        </ThreadPrimitive.Suggestion>
      ))}
    </div>
  </div>
);
