import { beforeEach, describe, expect, it } from 'vitest';
import { chatDocumentKey } from './pane-document';

describe('chatDocumentKey', () => {
  beforeEach(() => sessionStorage.clear());

  it('is the URL Word reports for a saved document', () => {
    expect(chatDocumentKey('https://contoso.sharepoint.com/Draft.docx')).toBe(
      'https://contoso.sharepoint.com/Draft.docx',
    );
  });

  it('gives an unsaved document a key of its own pane, kept across reloads', () => {
    const first = chatDocumentKey('');

    expect(first).toMatch(/^unsaved:[0-9a-f-]{36}$/);
    expect(chatDocumentKey('')).toBe(first);
    sessionStorage.clear();
    expect(chatDocumentKey('')).not.toBe(first);
  });
});
