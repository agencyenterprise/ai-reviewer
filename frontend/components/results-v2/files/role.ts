import { FileListItem, FileRole } from '@/lib/generated-api';

/** The three kinds of file a project holds, as the tab groups them. */
export type FileGroup = 'main' | 'source' | 'memo';

export const GROUP: Record<FileGroup, { label: string; plural: string; description: string; className: string }> = {
  main: {
    label: 'Main document',
    plural: 'Main document',
    description: 'The draft under review. Every assessment reads this document, and it is what the explorer shows.',
    className: 'bg-primary/10 text-primary',
  },
  source: {
    label: 'Source',
    plural: 'Sources',
    description: 'A document one of your references cites. Assessments that check citations read it.',
    className: 'bg-secondary text-secondary-foreground',
  },
  memo: {
    label: 'Reviewer memo',
    plural: 'Reviewer memos',
    description: 'Peer-review feedback on a draft, read by the Peer Review assessments.',
    className: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200',
  },
};

/** Supporting candidates are filtered out before this, and read as sources if any slip through. */
export function fileGroup(role: FileRole): FileGroup {
  if (role === FileRole.Main) return 'main';
  if (role === FileRole.ReviewerMemo) return 'memo';
  return 'source';
}

/** The line under a role tag: which revision this file belongs to, and whether it still stands. */
export function revisionLabel(file: FileListItem, currentRevision: number): string | null {
  if (file.revision == null) return null;
  if (file.role !== FileRole.Main) return `Revision ${file.revision}`;
  return file.revision === currentRevision
    ? `Revision ${file.revision} · current`
    : `Revision ${file.revision} · superseded`;
}

/** Main first (newest revision first), then memos, then sources by name. */
export function sortFiles(files: FileListItem[]): FileListItem[] {
  const rank = (role: FileRole) => (role === FileRole.Main ? 0 : role === FileRole.ReviewerMemo ? 1 : 2);
  return [...files].sort((a, b) => {
    const byRank = rank(a.role) - rank(b.role);
    if (byRank !== 0) return byRank;
    if (a.role === FileRole.Main && b.role === FileRole.Main) return (b.revision ?? 0) - (a.revision ?? 0);
    return (a.file_name || '').localeCompare(b.file_name || '');
  });
}
