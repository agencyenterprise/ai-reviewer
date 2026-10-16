import { FileListItem, FileRole } from '@/lib/generated-api';

/** A row the upload could have created for this staged file: same name, same bytes. */
const couldBe = (row: FileListItem, file: File) => row.file_name === file.name && row.file_size === file.size;

/**
 * Which project file each finished upload created.
 *
 * The upload reports which staged files finished, in the order they finished,
 * but not the ids of the files it created. So the candidates are the review
 * documents that appeared since it started (which keeps out a file someone
 * else added meanwhile) with a finished file's name and size. When two staged
 * files share both, the n-th file to finish takes the n-th such row by
 * creation time. That almost always pairs them right: the server creates each
 * row as that file's upload completes. Two uploads finishing within moments
 * can still commit and answer in opposite orders and swap; only an id
 * returned by the upload would rule that out.
 */
export function matchUploads(
  finished: File[],
  before: ReadonlySet<string>,
  after: FileListItem[],
): Map<File, FileListItem> {
  const fresh = after
    .filter((row) => !before.has(row.id) && row.role === FileRole.ReviewInput)
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
  const taken = new Set<string>();
  const matched = new Map<File, FileListItem>();
  for (const file of finished) {
    const row = fresh.find((candidate) => !taken.has(candidate.id) && couldBe(candidate, file));
    if (!row) continue;
    taken.add(row.id);
    matched.set(file, row);
  }
  return matched;
}

/** The uploaded rows in the order the files were sent: reviewer letters follow it. */
export function inSentOrder(sent: File[], matched: Map<File, FileListItem>): FileListItem[] {
  return sent.flatMap((file) => {
    const row = matched.get(file);
    return row ? [row] : [];
  });
}
