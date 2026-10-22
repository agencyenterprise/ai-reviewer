import { describe, expect, it } from 'vitest';
import type { HandoffView } from '@/lib/generated-api';
import { teamsNotice } from './teams-notice';

const handoff = (url: string): HandoffView => ({ document_url: url, document_name: 'Draft.docx' }) as HandoffView;

describe('teamsNotice', () => {
  it('says nothing when nothing waits', () => {
    expect(teamsNotice([], [])).toBeNull();
  });

  it('counts what waits on this document first', () => {
    expect(teamsNotice([handoff('a'), handoff('a')], [handoff('b')])).toBe(
      '2 suggestions from Teams for this document',
    );
    expect(teamsNotice([handoff('a')], [])).toBe('1 suggestion from Teams for this document');
  });

  it('otherwise counts the other documents, not the requests about them', () => {
    expect(teamsNotice([], [handoff('b'), handoff('b'), handoff('c')])).toBe(
      'Suggestions from Teams wait on 2 other documents',
    );
  });
});
