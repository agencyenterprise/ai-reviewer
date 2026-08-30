'use client';

import { formatFileSize } from '@/components/analysis-form/utils';
import { PeerReviewFacts } from '@/components/results/tabs/peer-review/peer-review-derive';
import { useRemoveFileMutation } from '@/components/results/tabs/reference-review/mutations';
import { FileTypeIcon } from '@/components/shared/file-type-icon';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { FileDownloadLink } from '@/components/ui/file-download-link';
import { FileListItem } from '@/lib/generated-api';
import { Loader2, Trash2, Upload } from 'lucide-react';
import { useState } from 'react';

interface MemosPaneProps {
  facts: PeerReviewFacts;
  projectId: string;
  readOnly: boolean;
  onUploadMemos: () => void;
}

/**
 * The reviewer memos every step reads from. A pane rather than a card above
 * the steps: it is the input to all four of them, so it belongs beside the
 * work rather than scrolling away above it.
 */
export function MemosPane({ facts, projectId, readOnly, onUploadMemos }: MemosPaneProps) {
  const { activeMemos, reviewedRevision, staleMemoRevisions, memos } = facts;
  const ignored = memos.filter((memo) => memo.revision !== reviewedRevision);

  return (
    <div className="flex h-full flex-col">
      <div className="bg-background/90 sticky top-0 z-10 flex h-10 shrink-0 items-center gap-2 border-b px-4 backdrop-blur">
        <span className="text-xs font-medium">Reviewer memos</span>
        <span className="font-mono text-[11px] tabular-nums text-muted-foreground">{activeMemos.length}</span>
        {!readOnly && (
          <Button size="xs" variant="outline" className="ml-auto" onClick={onUploadMemos}>
            <Upload className="size-3" />
            Add
          </Button>
        )}
      </div>

      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-4">
        <section>
          <h3 className="mb-2 font-mono text-[10px] tracking-wide text-muted-foreground uppercase">
            On revision {reviewedRevision}
          </h3>
          <ul className="space-y-1.5">
            {activeMemos.map((memo) => (
              <MemoRow key={memo.id} memo={memo} projectId={projectId} readOnly={readOnly} />
            ))}
          </ul>
        </section>

        {ignored.length > 0 && (
          // `max()` is not "most recently uploaded": memos targeting an older
          // revision than an existing batch are silently ignored by the agent.
          // Unexplained, that behaviour is inexplicable — so say it, and list
          // them here so it can be acted on without leaving the tab.
          <section>
            <h3 className="mb-2 font-mono text-[10px] tracking-wide text-amber-700 uppercase dark:text-amber-400">
              Not being read
            </h3>
            <p className="mb-2 text-[11.5px] leading-relaxed text-muted-foreground">
              {ignored.length} memo{ignored.length === 1 ? '' : 's'} on revision {staleMemoRevisions.join(', ')}{' '}
              {ignored.length === 1 ? 'is' : 'are'} ignored — the steps read only revision {reviewedRevision}, the most
              recent draft that has any. Remove {ignored.length === 1 ? 'it' : 'them'}, or upload again targeting
              revision {reviewedRevision}.
            </p>
            <ul className="space-y-1.5 opacity-70">
              {ignored.map((memo) => (
                <MemoRow key={memo.id} memo={memo} projectId={projectId} readOnly={readOnly} showRevision />
              ))}
            </ul>
          </section>
        )}
      </div>
    </div>
  );
}

function MemoRow({
  memo,
  projectId,
  readOnly,
  showRevision = false,
}: {
  memo: FileListItem;
  projectId: string;
  readOnly: boolean;
  /** Ignored memos can span several revisions, so each says which it belongs to. */
  showRevision?: boolean;
}) {
  const [removeOpen, setRemoveOpen] = useState(false);
  const removeFile = useRemoveFileMutation(projectId, memo.id);

  return (
    <li className="flex items-center gap-2 rounded-md border px-2.5 py-2">
      <FileTypeIcon fileType={memo.file_type} className="size-3.5 shrink-0 text-muted-foreground" />
      <FileDownloadLink fileId={memo.id} className="text-primary min-w-0 flex-1 truncate text-[12.5px] hover:underline">
        {memo.file_name || 'Unknown'}
      </FileDownloadLink>
      {showRevision && memo.revision != null && (
        <span className="bg-muted shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
          Rev {memo.revision}
        </span>
      )}
      <span className="shrink-0 font-mono text-[10px] tabular-nums text-muted-foreground">
        {formatFileSize(memo.file_size)}
      </span>

      {!readOnly && (
        <>
          <Button
            size="icon"
            variant="ghost"
            className="size-6 shrink-0"
            disabled={removeFile.isPending}
            onClick={() => setRemoveOpen(true)}
            aria-label="Remove memo"
          >
            {removeFile.isPending ? (
              <Loader2 className="size-3 animate-spin" />
            ) : (
              <Trash2 className="size-3 text-muted-foreground" />
            )}
          </Button>

          <AlertDialog open={removeOpen} onOpenChange={setRemoveOpen}>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Remove this reviewer memo?</AlertDialogTitle>
                <AlertDialogDescription className="break-all">
                  {memo.file_name} will be removed from the project. Steps you run afterwards will no longer read it.
                  Reports already generated are unaffected.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={() => removeFile.mutate()}>Remove</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </>
      )}
    </li>
  );
}
