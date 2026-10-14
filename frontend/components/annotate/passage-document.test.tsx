import { afterEach, describe, expect, it } from 'vitest';
import { renderInto, Rendered } from '@/lib/test-render';
import { PassageDocument, passageRow } from './passage-document';

const DOCUMENT = [
  '# Scope',
  '',
  'We surveyed three states.',
  '',
  'Off-grid approaches, sometimes called bridge power,[[9]](#footnote-10) were not considered.',
].join('\n');

let rendered: Rendered | null = null;
afterEach(async () => {
  await rendered?.unmount();
  rendered = null;
});

/** The source line of the row the pane picks for the passage, or null when it picks none. */
async function pickedLine(anchor: string, line: number): Promise<string | null> {
  rendered = await renderInto(<PassageDocument document={DOCUMENT} anchor={anchor} line={line} />);
  const row = passageRow(rendered.container, line);
  return row?.querySelector<HTMLElement>('[data-block-owner]')?.dataset.lineStart ?? null;
}

describe('passageRow', () => {
  it('picks the paragraph of an anchor quoted with a footnote link', async () => {
    const anchor = 'Off-grid approaches, sometimes called bridge power,[[9]](#footnote-10) were not considered';
    expect(await pickedLine(anchor, 5)).toBe('5');
  });

  it('picks the row where the anchor was found, not the stated line', async () => {
    expect(await pickedLine('three states', 5)).toBe('3');
  });

  it('falls back to the source line when the anchor cannot be found', async () => {
    expect(await pickedLine('text that is not there', 3)).toBe('3');
  });
});
