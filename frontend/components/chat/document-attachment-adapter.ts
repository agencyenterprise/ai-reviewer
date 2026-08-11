import type { AttachmentAdapter, CompleteAttachment, PendingAttachment } from '@assistant-ui/react';

const PDF_TYPE = 'application/pdf';
const DOCX_TYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

/**
 * Attachment adapter for PDF and DOCX documents.
 *
 * Text extraction runs server-side: `send()` uploads the file to `/api/extract`
 * and turns the returned text into a message text part, so the chat model (and
 * the Draft Detective skills) can review the document's contents.
 */
export class DocumentAttachmentAdapter implements AttachmentAdapter {
  accept = `${PDF_TYPE},.pdf,${DOCX_TYPE},.docx`;

  async add({ file }: { file: File }): Promise<PendingAttachment> {
    return {
      id: crypto.randomUUID(),
      type: 'document',
      name: file.name,
      contentType: file.type,
      file,
      // Defer extraction until the message is sent.
      status: { type: 'requires-action', reason: 'composer-send' },
    };
  }

  async send(attachment: PendingAttachment): Promise<CompleteAttachment> {
    const form = new FormData();
    form.append('file', attachment.file, attachment.name);

    const response = await fetch('/api/extract', { method: 'POST', body: form });
    if (!response.ok) {
      const detail = (await response.json().catch(() => null)) as { error?: string } | null;
      throw new Error(detail?.error ?? `Could not read "${attachment.name}".`);
    }

    const { text } = (await response.json()) as { text: string };

    return {
      id: attachment.id,
      type: attachment.type,
      name: attachment.name,
      contentType: attachment.contentType,
      content: [
        {
          type: 'text',
          text: `Attached document "${attachment.name}":\n\n${text}`,
        },
      ],
      status: { type: 'complete' },
    };
  }

  async remove(): Promise<void> {
    // Nothing to clean up — the file is only uploaded on send.
  }
}
