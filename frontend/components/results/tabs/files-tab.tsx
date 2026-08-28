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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { FileDownloadLink } from '@/components/ui/file-download-link';
import { useExperimentalFeatures } from '@/context/experimental-features-context';
import { useDownloadAllProjectFiles } from '@/hooks/use-download-all-project-files';
import { buildReferenceByFileIdMap, composeReferences, ComposedReference } from '@/lib/composed-references';
import { FileListItem, FileRole, ProjectDetailed, WorkflowRunType } from '@/lib/generated-api';
import { getWorkflowRunByType } from '@/lib/workflow-state';
import { Download, Loader2, MoreVerticalIcon, RefreshCw, Search, Trash2, Upload } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useRemoveFileMutation } from './reference-review/mutations';
import { ReplaceMainDocumentDialog } from '../components/replace-main-document-dialog';
import { FileUploadDialog } from './reference-review/file-upload-dialog';

interface FilesTabProps {
  projectDetail: ProjectDetailed;
  readOnly?: boolean;
  onRevisionCreated?: () => void;
}

function FileNameLink({ file }: { file: FileListItem }) {
  if (!file.id) {
    return (
      <div className="flex items-center gap-2">
        <FileTypeIcon fileType={file.file_type} />
        <span>{file.file_name || 'Unknown'}</span>
      </div>
    );
  }

  return (
    <FileDownloadLink fileId={file.id} className="text-blue-600 hover:underline flex items-center gap-2">
      <FileTypeIcon fileType={file.file_type} />
      {file.file_name || 'Unknown'}
    </FileDownloadLink>
  );
}

function RoleTag({
  role,
  detail,
  variant,
}: {
  role: string;
  detail?: string;
  variant: 'main' | 'muted' | 'support' | 'memo';
}) {
  const variantClass =
    variant === 'main'
      ? 'bg-primary/10 text-primary'
      : variant === 'muted'
        ? 'bg-muted text-muted-foreground'
        : variant === 'memo'
          ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200'
          : 'bg-secondary text-secondary-foreground';
  return (
    <span className={`inline-flex flex-col items-start rounded-md px-2.5 py-1 leading-tight ${variantClass}`}>
      <span className="text-xs font-semibold">{role}</span>
      {detail && <span className="text-[10px] font-medium opacity-70">{detail}</span>}
    </span>
  );
}

interface FileTableRowProps {
  file: FileListItem;
  projectId: string;
  currentRevision: number;
  matchedReference?: ComposedReference;
  onReplaceMain?: () => void;
}

function FileTableRow({ file, projectId, currentRevision, matchedReference, onReplaceMain }: FileTableRowProps) {
  const isMain = file.role === FileRole.Main;
  const isCurrentMain = isMain && file.revision === currentRevision;
  const removeFileMutation = useRemoveFileMutation(projectId, file.id);
  const isRemoving = removeFileMutation.isPending;

  return (
    <TableRow key={file.id}>
      <TableCell className="whitespace-normal break-all align-middle">
        <FileNameLink file={file} />
        {matchedReference && (
          <p className="mt-1 ml-6 text-xs text-muted-foreground line-clamp-2" title={matchedReference.text}>
            <span className="font-medium">Matched reference: </span>
            <span className="italic">{matchedReference.text}</span>
          </p>
        )}
      </TableCell>
      <TableCell className="align-middle">
        {isMain ? (
          <RoleTag
            role="Main"
            detail={isCurrentMain ? 'Current revision' : `Revision ${file.revision ?? '?'}`}
            variant={isCurrentMain ? 'main' : 'muted'}
          />
        ) : file.role === FileRole.ReviewerMemo ? (
          <RoleTag
            role="Reviewer memo"
            detail={file.revision != null ? `Revision ${file.revision}` : undefined}
            variant="memo"
          />
        ) : (
          <RoleTag role="Supporting" variant="support" />
        )}
      </TableCell>
      <TableCell className="text-xs text-right align-middle">{formatFileSize(file.file_size)}</TableCell>
      <TableCell>
        {isMain && !isCurrentMain ? null : (
          <AlertDialog>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="size-8" disabled={isRemoving}>
                  {isRemoving ? <Loader2 className="size-4 animate-spin" /> : <MoreVerticalIcon className="size-4" />}
                  <span className="sr-only">Open menu</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {isCurrentMain && onReplaceMain ? (
                  <DropdownMenuItem onClick={onReplaceMain}>
                    <RefreshCw className="size-4" />
                    Replace document
                  </DropdownMenuItem>
                ) : (
                  <AlertDialogTrigger asChild>
                    <DropdownMenuItem disabled={isMain} variant="destructive">
                      <Trash2 className="size-4" />
                      Remove file
                    </DropdownMenuItem>
                  </AlertDialogTrigger>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Remove file?</AlertDialogTitle>
                <AlertDialogDescription className="break-all">
                  Are you sure you want to remove &quot;{file.file_name}&quot; from this project? This action cannot be
                  undone. The associated reference (if any) will become unmatched.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={() => removeFileMutation.mutate()}>Remove</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </TableCell>
    </TableRow>
  );
}

export function FilesTab({ projectDetail, readOnly = false, onRevisionCreated }: FilesTabProps) {
  const projectId = projectDetail.project.id;
  const currentRevision = projectDetail.project.current_revision ?? 1;
  const files = useMemo(() => projectDetail.files ?? [], [projectDetail.files]);
  const workflowDetails = useMemo(() => projectDetail.workflow_runs ?? [], [projectDetail.workflow_runs]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isReplaceDialogOpen, setIsReplaceDialogOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  // Reviewer memos only feed the alpha Peer Review tab, so the role picker is
  // offered to the same users who can see that tab.
  const { showExperimentalFeatures } = useExperimentalFeatures();

  const referenceExtraction = getWorkflowRunByType(workflowDetails, WorkflowRunType.ReferenceExtraction);
  const referenceFileMatching = getWorkflowRunByType(workflowDetails, WorkflowRunType.ReferenceFileMatching);

  const { downloadAll, isDownloading } = useDownloadAllProjectFiles(projectId);

  // Compose references from extraction and file matching states
  const composedReferences = useMemo(
    () =>
      composeReferences(referenceExtraction?.state?.extracted_references, referenceFileMatching?.state?.matches, files),
    [referenceExtraction?.state?.extracted_references, referenceFileMatching?.state?.matches, files],
  );

  // Build a map of file_id to matched references once
  const matchedReferencesMap = useMemo(() => buildReferenceByFileIdMap(composedReferences), [composedReferences]);

  // Sort files: main documents first (current revision, then older revisions
  // newest-first), then reviewer memos, then supporting files alphabetically.
  const roleRank = (role: FileListItem['role']) =>
    role === FileRole.Main ? 0 : role === FileRole.ReviewerMemo ? 1 : 2;
  const sortedFiles = useMemo(
    () =>
      [...(files || [])].sort((a, b) => {
        const rankDiff = roleRank(a.role) - roleRank(b.role);
        if (rankDiff !== 0) return rankDiff;
        if (a.role === FileRole.Main && b.role === FileRole.Main) {
          return (b.revision ?? 0) - (a.revision ?? 0);
        }
        return (a.file_name || '').localeCompare(b.file_name || '');
      }),
    [files],
  );

  // Filter files based on search query
  const filteredFiles = useMemo(() => {
    if (!searchQuery.trim()) return sortedFiles;
    const query = searchQuery.toLowerCase();
    return sortedFiles.filter((file) => {
      const matchedReference = file.id ? matchedReferencesMap.get(file.id) : undefined;
      return (
        file.file_name?.toLowerCase().includes(query) ||
        file.description?.toLowerCase().includes(query) ||
        matchedReference?.text?.toLowerCase().includes(query)
      );
    });
  }, [sortedFiles, searchQuery, matchedReferencesMap]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          Project Files ({filteredFiles.length}
          {searchQuery ? ` of ${sortedFiles.length}` : ''})
        </h2>
        <div className="flex items-center gap-2">
          {!readOnly && (
            <Button onClick={() => setIsUploadOpen(true)} variant="outline" size="sm">
              <Upload className="size-4" />
              Upload files
            </Button>
          )}
          {sortedFiles.length > 0 && (
            <Button onClick={downloadAll} disabled={isDownloading} variant="outline" size="sm">
              {isDownloading ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Downloading...
                </>
              ) : (
                <>
                  <Download className="size-4" />
                  Download all files (.zip)
                </>
              )}
            </Button>
          )}
        </div>
      </div>

      {sortedFiles.length > 0 && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder="Search by file name, description, or matched reference..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      )}

      {sortedFiles.length === 0 ? (
        <div className="text-sm text-muted-foreground">No files uploaded.</div>
      ) : (
        <Table className="table-fixed w-full overflow-x-visible">
          <colgroup>
            <col className="w-[75%]" />
            <col className="w-[10%]" />
            <col className="w-[10%]" />
            <col className="w-[5%]" />
          </colgroup>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Role</TableHead>
              <TableHead className="text-right">Size</TableHead>
              <TableHead className="w-8"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredFiles.map((file) => (
              <FileTableRow
                key={file.id}
                file={file}
                projectId={projectId}
                currentRevision={currentRevision}
                matchedReference={file.id ? matchedReferencesMap.get(file.id) : undefined}
                onReplaceMain={readOnly ? undefined : () => setIsReplaceDialogOpen(true)}
              />
            ))}
          </TableBody>
        </Table>
      )}

      <ReplaceMainDocumentDialog
        isOpen={isReplaceDialogOpen}
        projectId={projectId}
        onClose={() => setIsReplaceDialogOpen(false)}
        onRevisionCreated={onRevisionCreated}
      />

      <FileUploadDialog
        isOpen={isUploadOpen}
        projectId={projectId}
        title="Upload files"
        description={
          showExperimentalFeatures
            ? 'Add supporting documents or reviewer memos to this project.'
            : 'Add supporting documents to this project.'
        }
        multiple
        allowRoleSelection={showExperimentalFeatures}
        allowRevisionSelection
        currentRevision={currentRevision}
        onCancel={() => setIsUploadOpen(false)}
        onComplete={() => setIsUploadOpen(false)}
      />
    </div>
  );
}
