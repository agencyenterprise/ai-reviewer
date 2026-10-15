import JSZip from 'jszip';
import { describe, expect, it } from 'vitest';
import { markdownToDocx } from './markdown-docx';

/** The `<w:p>` elements of the generated document, as XML strings. */
async function paragraphsOf(markdown: string): Promise<string[]> {
  const zip = await JSZip.loadAsync(await (await markdownToDocx(markdown)).arrayBuffer());
  const xml = (await zip.file('word/document.xml')?.async('string')) ?? '';
  return xml.match(/<w:p>[\s\S]*?<\/w:p>/g) ?? [];
}

/** Each run of a paragraph as its text, prefixed with "⏎" when it opens with a line break. */
function runsOf(paragraph: string): string[] {
  return (paragraph.match(/<w:r>[\s\S]*?<\/w:r>/g) ?? []).map((run) => {
    const text = run.match(/<w:t[^>]*>([\s\S]*?)<\/w:t>/)?.[1] ?? '';
    return `${run.includes('<w:br/>') ? '⏎' : ''}${text}`;
  });
}

async function quoteRuns(markdown: string): Promise<string[][]> {
  const paragraphs = await paragraphsOf(markdown);
  return paragraphs.filter((p) => p.includes('w:left="720"')).map(runsOf);
}

// Word ignores "\n" inside a run, so the patched library splits blockquote
// lines into runs separated by <w:br/> (patches/@mohtasham__md-to-docx@*.patch).
describe('markdownToDocx blockquotes', () => {
  it('keeps soft line breaks as Word line breaks', async () => {
    expect(await quoteRuns('> line one\n> line two\n> line three')).toEqual([['line one', '⏎line two', '⏎line three']]);
  });

  it('keeps hard line breaks as Word line breaks', async () => {
    const runs = await quoteRuns('> line one  \n> line two\\\n> line three');
    expect(runs).toHaveLength(1);
    expect(runs[0].join('')).toBe('line one⏎line two⏎line three');
  });

  it('keeps separate quote paragraphs separate', async () => {
    expect(await quoteRuns('> first\n> more\n>\n> second')).toEqual([['first', '⏎more'], ['second']]);
  });

  it('leaves line breaks outside blockquotes alone', async () => {
    const paragraphs = await paragraphsOf('plain one\nplain two');
    expect(paragraphs.some((p) => p.includes('<w:br/>'))).toBe(false);
  });
});
