import { describe, expect, it } from 'vitest';
import { downloadRequest, initialChoices } from './share-warning-dialog';

describe('downloadRequest', () => {
  it('a private project downloads plain comments, with edits, by default', () => {
    expect(downloadRequest(initialChoices(false), true)).toEqual({
      type: 'comments',
      options: { includeEdits: true },
    });
  });

  it('a public project links its comments by default', () => {
    expect(downloadRequest(initialChoices(true), true).type).toBe('comments-with-links');
  });

  it('asking for links on a private project links them', () => {
    expect(downloadRequest({ ...initialChoices(false), addLinks: true }, true).type).toBe('comments-with-links');
  });

  it('never asks for links the backend would drop', () => {
    expect(downloadRequest(initialChoices(true), false).type).toBe('comments');
    expect(downloadRequest({ ...initialChoices(false), addLinks: true }, false).type).toBe('comments');
  });

  it('edits can be left out', () => {
    expect(downloadRequest({ ...initialChoices(false), includeEdits: false }, true)).toEqual({
      type: 'comments',
      options: { includeEdits: false },
    });
  });
});
