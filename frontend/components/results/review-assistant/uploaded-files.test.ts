import { describe, expect, it } from 'vitest';
import { FileListItem, FileRole } from '@/lib/generated-api';
import { inSentOrder, matchUploads } from './uploaded-files';

const staged = (name: string, body: string) => new File([body], name);

function row(id: string, file: File, createdAt: string, role: FileRole = FileRole.ReviewInput): FileListItem {
  return {
    id,
    project_id: 'p',
    file_name: file.name,
    file_path: `/uploads/${id}`,
    file_type: 'text/plain',
    file_size: file.size,
    content_hash: id,
    role,
    // The API sends ISO strings where the generated type says Date.
    created_at: createdAt as unknown as Date,
  };
}

describe('matchUploads', () => {
  it('pairs only the files that finished, leaving a failed twin staged', () => {
    const first = staged('report.docx', 'aaaa');
    const second = staged('report.docx', 'bbbb'); // same name and size
    const created = row('r1', second, '2026-10-16T10:00:00Z');

    const matched = matchUploads([second], new Set(), [created]);

    expect(matched.get(second)?.id).toBe('r1');
    expect(matched.has(first)).toBe(false);
  });

  it('gives look-alike files their rows in the order they finished', () => {
    const first = staged('report.docx', 'aaaa');
    const second = staged('report.docx', 'bbbb');
    // The listing comes back in no set order; creation time follows finishing.
    const rows = [row('later', first, '2026-10-16T10:00:05Z'), row('earlier', second, '2026-10-16T10:00:01Z')];

    const matched = matchUploads([second, first], new Set(), rows);

    expect(matched.get(second)?.id).toBe('earlier');
    expect(matched.get(first)?.id).toBe('later');
  });

  it('ignores rows that were there before, or that are not review documents', () => {
    const file = staged('memo.md', 'text');
    const rows = [
      row('old', file, '2026-10-16T09:00:00Z'),
      row('source', file, '2026-10-16T10:00:00Z', FileRole.Support),
    ];

    expect(matchUploads([file], new Set(['old']), rows).size).toBe(0);
  });
});

describe('inSentOrder', () => {
  it('lists the uploaded rows in the order the author added the files', () => {
    const a = staged('a.md', 'a');
    const b = staged('b.md', 'b');
    const matched = matchUploads([b, a], new Set(), [
      row('rb', b, '2026-10-16T10:00:00Z'),
      row('ra', a, '2026-10-16T10:00:01Z'),
    ]);

    expect(inSentOrder([a, b], matched).map((r) => r.id)).toEqual(['ra', 'rb']);
  });
});
