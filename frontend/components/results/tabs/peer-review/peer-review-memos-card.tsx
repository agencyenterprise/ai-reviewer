'use client';

import { formatFileSize } from '@/components/analysis-form/utils';
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
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Callout } from '@/components/ui/callout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileDownloadLink } from '@/components/ui/file-download-link';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { FileListItem } from '@/lib/generated-api';
import { AlertTriangle, Loader2, Trash2, Upload } from 'lucide-react';
import { useRemoveFileMutation } from '../reference-review/mutations';
import { PeerReviewFacts } from './peer-review-derive';

interface PeerReviewMemosCardProps {
  facts: PeerReviewFacts;
  projectId: string;
  readOnly: boolean;
  onUploadMemos: () => void;
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
  const removeFileMutation = useRemoveFileMutation(projectId, memo.id);
  const isRemoving = removeFileMutation.isPending;

  return (
    <li className="flex items-center gap-3 rounded-md border px-3 py-2">
      <FileTypeIcon fileType={memo.file_type} />
      <FileDownloadLink fileId={memo.id} className="min-w-0 flex-1 truncate text-sm hover:underline">
        {memo.file_name || 'Unknown'}
      </FileDownloadLink>
      {showRevision && memo.revision != null && (
        <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
          Revision {memo.revision}
        </span>
      )}
      <span className="shrink-0 text-xs text-muted-foreground">{formatFileSize(memo.file_size)}</span>
      {!readOnly && (
        <AlertDialog>
          <Tooltip>
            <TooltipTrigger asChild>
              <AlertDialogTrigger asChild>
                <Button variant="ghost" size="icon" className="size-8 shrink-0" disabled={isRemoving}>
                  {isRemoving ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Trash2 className="size-4 text-muted-foreground" />
                  )}
                  <span className="sr-only">Remove memo</span>
                </Button>
              </AlertDialogTrigger>
            </TooltipTrigger>
            <TooltipContent>Remove memo</TooltipContent>
          </Tooltip>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Remove reviewer memo?</AlertDialogTitle>
              <AlertDialogDescription className="break-all">
                &quot;{memo.file_name}&quot; will be removed from this project. This cannot be undone, and assessments
                you run afterwards will no longer read it. Reports already generated are unaffected.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={() => removeFileMutation.mutate()}>Remove</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </li>
  );
}

export function PeerReviewMemosCard({ facts, projectId, readOnly, onUploadMemos }: PeerReviewMemosCardProps) {
  const { activeMemos, reviewedRevision, staleMemoRevisions, memos } = facts;
  const ignoredMemos = memos.filter((memo) => memo.revision !== reviewedRevision);

  return (
    <Card className="gap-3">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm">
          {activeMemos.length} reviewer {activeMemos.length === 1 ? 'memo' : 'memos'} on revision {reviewedRevision}
        </CardTitle>
        {!readOnly && (
          <Button variant="outline" size="sm" onClick={onUploadMemos}>
            <Upload className="size-4" />
            Add memos
          </Button>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        <ul className="space-y-2">
          {activeMemos.map((memo) => (
            <MemoRow key={memo.id} memo={memo} projectId={projectId} readOnly={readOnly} />
          ))}
        </ul>

        {ignoredMemos.length > 0 && (
          // `max()` is not "most recently uploaded": memos targeting an older
          // revision than an existing batch are silently ignored by the agent.
          // Without saying so, that behaviour is inexplicable — and they are
          // listed below so the advice can be acted on without leaving the tab.
          <div className="space-y-2">
            <Callout variant="warning" icon={AlertTriangle} title="Some memos are not being used">
              <p className="text-sm">
                {ignoredMemos.length} memo{ignoredMemos.length === 1 ? '' : 's'} on revision{' '}
                {staleMemoRevisions.join(', ')} {ignoredMemos.length === 1 ? 'is' : 'are'} ignored. The assessments read
                only the memos on revision {reviewedRevision}, the most recent draft that has any. Remove them, or
                re-upload them targeting revision {reviewedRevision}, to include them.
              </p>
            </Callout>
            <ul className="space-y-2 opacity-70">
              {ignoredMemos.map((memo) => (
                <MemoRow key={memo.id} memo={memo} projectId={projectId} readOnly={readOnly} showRevision />
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
