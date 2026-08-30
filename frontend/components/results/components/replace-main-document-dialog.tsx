'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { getErrorMessage } from '@/lib/api-error';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { HelpLink } from '@/components/help/help-link';
import { Label } from '@/components/ui/label';
import { FileUpload } from '@/components/ui/file-upload';
import { FileListItem } from '@/components/analysis-form/file-list-item';
import { uploadSingleFile, formatBytes, type UploadProgress } from '@/lib/hooks/upload';
import {
  createRevisionEndpointApiProjectProjectIdRevisionsPost,
  FileRole,
  startMultipleWorkflowsApiWorkflowsStartMultiplePost,
  WorkflowRunType,
} from '@/lib/generated-api';
import { MAX_FILE_SIZE_BYTES } from '@/lib/constants';
import { Loader2 } from 'lucide-react';

const INITIAL_WORKFLOWS = [
  WorkflowRunType.DocumentProcessing,
  WorkflowRunType.ReferenceExtraction,
  WorkflowRunType.DocumentSummarization,
];

type Stage = 'select' | 'creating-revision' | 'uploading' | 'starting-workflows' | 'complete';

export interface ReplaceMainDocumentDialogProps {
  isOpen: boolean;
  projectId: string;
  onClose: () => void;
  /** Called after a new revision is successfully created, so the caller can
   *  switch the view to the newly created (now current) revision. */
  onRevisionCreated?: () => void;
  /**
   * Hides the "re-run previous assessments" choice. The Peer Review tab sets
   * this: there, uploading a revised draft is one step of a sequence whose next
   * steps the user starts deliberately, so an extra toggle about unrelated
   * assessments is noise. Document processing still runs either way.
   */
  hideRerunOption?: boolean;
}

export function ReplaceMainDocumentDialog({
  isOpen,
  projectId,
  onClose,
  onRevisionCreated,
  hideRerunOption = false,
}: ReplaceMainDocumentDialogProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [rerunAnalyses, setRerunAnalyses] = useState(true);
  // Hiding the control also disables the behaviour: only document processing
  // and the other initial workflows run.
  const shouldRerunAnalyses = rerunAnalyses && !hideRerunOption;
  const [stage, setStage] = useState<Stage>('select');
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const queryClient = useQueryClient();
  const abortRef = useRef(false);

  useEffect(() => {
    if (isOpen) {
      setSelectedFile(null);
      setRerunAnalyses(true);
      setStage('select');
      setUploadProgress(null);
      abortRef.current = false;
    }
  }, [isOpen]);

  const replaceMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile) throw new Error('No file selected');

      // Step 1: Create new revision
      setStage('creating-revision');
      const { previous_workflow_types } = await createRevisionEndpointApiProjectProjectIdRevisionsPost({
        path: { project_id: projectId },
      });

      if (abortRef.current) return;

      // Step 2: Upload new main document
      setStage('uploading');
      await uploadSingleFile(selectedFile, {
        projectId,
        fileRole: FileRole.Main,
        onProgress: setUploadProgress,
      });

      if (abortRef.current) return;

      // Step 3: Start workflows if requested
      if (shouldRerunAnalyses && previous_workflow_types.length > 0) {
        setStage('starting-workflows');
        const initialSet = new Set<string>(INITIAL_WORKFLOWS);
        const workflowTypes = [
          ...INITIAL_WORKFLOWS,
          ...previous_workflow_types.filter((t: WorkflowRunType) => !initialSet.has(t)),
        ];
        await startMultipleWorkflowsApiWorkflowsStartMultiplePost({
          body: { project_id: projectId, workflow_types: workflowTypes },
        });
      } else {
        // Always run initial processing workflows
        setStage('starting-workflows');
        await startMultipleWorkflowsApiWorkflowsStartMultiplePost({
          body: { project_id: projectId, workflow_types: INITIAL_WORKFLOWS },
        });
      }

      setStage('complete');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      // Follow the newly created revision so the view doesn't stay pinned to
      // the previous one.
      onRevisionCreated?.();
      toast.success(shouldRerunAnalyses ? 'New revision created. Assessments started.' : 'New revision created.');
      onClose();
    },
    onError: (error) => {
      setStage('select');
      toast.error(getErrorMessage(error, 'Failed to create revision'));
    },
  });

  const handleFilesChange = useCallback((files: File[]) => {
    setSelectedFile(files[0] || null);
  }, []);

  const handleClose = useCallback(() => {
    if (stage !== 'select' && stage !== 'complete') {
      abortRef.current = true;
    }
    onClose();
  }, [stage, onClose]);

  const isProcessing = stage !== 'select' && stage !== 'complete';
  const isValid = selectedFile && selectedFile.size <= MAX_FILE_SIZE_BYTES;

  const stageMessage = (() => {
    switch (stage) {
      case 'creating-revision':
        return 'Creating new revision...';
      case 'uploading':
        if (uploadProgress && selectedFile) {
          return `Uploading... ${uploadProgress.progress_percent}% (${formatBytes(uploadProgress.uploaded_size)} / ${formatBytes(selectedFile.size)})`;
        }
        return 'Uploading document...';
      case 'starting-workflows':
        return 'Starting assessment workflows...';
      default:
        return '';
    }
  })();

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && !isProcessing && handleClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Create a new revision</DialogTitle>
          <DialogDescription>
            A revision is a version of the main document. Uploading a new version here creates a new revision and makes
            it the current one. Your previous revisions, with all their related results, are kept and stay available.{' '}
            <HelpLink topic="revisions">More about revisions</HelpLink>
          </DialogDescription>
        </DialogHeader>

        {isProcessing ? (
          <div className="flex items-center gap-3 py-4">
            <Loader2 className="size-5 animate-spin text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{stageMessage}</span>
          </div>
        ) : (
          <div className="space-y-4 min-w-0">
            <div className="space-y-2">
              <Label>New version of the main document</Label>
              <FileUpload
                files={selectedFile ? [selectedFile] : []}
                onFilesChange={handleFilesChange}
                accept=".pdf,.doc,.docx,.txt,.md"
                multiple={false}
                maxSize={MAX_FILE_SIZE_BYTES / (1024 * 1024)}
                className="h-36"
                compact
              />
            </div>

            {selectedFile && (
              <div className="space-y-2">
                <FileListItem file={selectedFile} type={FileRole.Main} onRemove={() => setSelectedFile(null)} />
              </div>
            )}

            {!hideRerunOption && (
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="rerun-analyses"
                    checked={rerunAnalyses}
                    onCheckedChange={(checked) => setRerunAnalyses(checked === true)}
                  />
                  <Label htmlFor="rerun-analyses" className="text-sm font-normal cursor-pointer">
                    Re-run previous assessments on this revision
                  </Label>
                </div>
                <p className="text-xs text-muted-foreground pl-6">
                  Automatically run the same assessments on the new revision that were run on the previous one. If
                  unchecked, you can still start assessments manually later.
                </p>
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isProcessing}>
            Cancel
          </Button>
          <Button onClick={() => replaceMutation.mutate()} disabled={!isValid || isProcessing}>
            Create revision
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
