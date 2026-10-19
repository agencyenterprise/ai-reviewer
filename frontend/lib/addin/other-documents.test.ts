import { describe, expect, it } from 'vitest';
import type { HandoffView } from '@/lib/generated-api';
import { openInBrowser, waitingDocuments } from './other-documents';

const PATH = 'https://contoso.sharepoint.com/Documentos Compartilhados/Energy.docx';

function handoff(id: string, url: string, name = 'Energy.docx'): HandoffView {
  return {
    id,
    status: 'pending',
    document_name: name,
    document_url: url,
    items: {},
    created_at: new Date('2026-10-19T00:00:00Z'),
  };
}

describe('openInBrowser', () => {
  it('asks SharePoint to open a file link in Word for the web, not download it', () => {
    const opened = new URL(openInBrowser(PATH));
    expect(opened.searchParams.get('web')).toBe('1');
    expect(decodeURIComponent(opened.pathname)).toBe('/Documentos Compartilhados/Energy.docx');
  });

  it('leaves a link that already opens in the browser as it is', () => {
    const page = 'https://contoso.sharepoint.com/_layouts/15/Doc.aspx?sourcedoc=%7B1%7D&file=Energy.docx';
    expect(openInBrowser(page)).toBe(page);
    expect(openInBrowser(`${PATH}?web=1`)).toBe(`${PATH}?web=1`);
    expect(openInBrowser('not a url')).toBe('not a url');
  });
});

describe('waitingDocuments', () => {
  it('lists each document once, with how many sets wait for it', () => {
    const listed = waitingDocuments([
      handoff('a', PATH),
      handoff('b', PATH),
      handoff('c', 'https://contoso.sharepoint.com/Other.docx', 'Other.docx'),
    ]);

    expect(listed.map(({ name, count }) => [name, count])).toEqual([
      ['Energy.docx', 2],
      ['Other.docx', 1],
    ]);
    expect(new URL(listed[0].url).searchParams.get('web')).toBe('1');
  });
});
