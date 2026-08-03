'use client';

import { useAuiState, type ThreadMessage } from '@assistant-ui/react';
import { FileTextIcon } from 'lucide-react';
import { useMemo } from 'react';

interface MainDocument {
  name: string;
  text: string;
}

// The attachment adapter stores extracted text as `Attached document "<name>":\n\n<text>`.
// Strip that prefix so the panel shows just the document body.
const DOC_PREFIX = /^Attached document "[^"]*":\n\n/;

/**
 * Finds the first uploaded document in the thread by scanning messages in order
 * for an attachment carrying extracted text (see `DocumentAttachmentAdapter`).
 */
function findMainDocument(messages: readonly ThreadMessage[]): MainDocument | null {
  for (const message of messages) {
    for (const attachment of message.attachments ?? []) {
      const textPart = attachment.content.find((part) => part.type === 'text');
      if (textPart && textPart.type === 'text') {
        return { name: attachment.name, text: textPart.text.replace(DOC_PREFIX, '') };
      }
    }
  }
  return null;
}

/**
 * Read-only right-side panel showing the first document uploaded in the current
 * thread. Proof-of-concept: the text is derived from the thread's message
 * attachments; a richer source (revisions, structured view) can be plugged in
 * later.
 */
export function DocumentPanel() {
  const messages = useAuiState((state) => state.thread.messages);
  const doc = useMemo(() => findMainDocument(messages ?? []), [messages]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b px-4 py-3">
        <FileTextIcon className="size-4 shrink-0 text-muted-foreground" />
        <div className="min-w-0">
          <h2 className="text-sm font-medium leading-tight">Document</h2>
          {doc ? (
            <p className="truncate text-xs text-muted-foreground" title={doc.name}>
              {doc.name}
            </p>
          ) : (
            <p className="text-xs text-muted-foreground">Nothing uploaded yet</p>
          )}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
        {doc ? (
          <pre className="font-sans text-xs leading-relaxed whitespace-pre-wrap text-foreground">{doc.text}</pre>
        ) : (
          <p className="text-xs text-muted-foreground">
            Upload a PDF or DOCX in the chat and its text will appear here for reference.
          </p>
        )}
      </div>
    </div>
  );
}
