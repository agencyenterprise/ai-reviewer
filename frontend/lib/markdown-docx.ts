import { convertMarkdownToDocx } from '@mohtasham/md-to-docx';

/** Converts markdown to a DOCX blob in the house style used for exports. */
export function markdownToDocx(markdown: string): Promise<Blob> {
  return convertMarkdownToDocx(markdown, {
    style: {
      fontFamily: 'Georgia',
    },
  });
}
