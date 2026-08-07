'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { getErrorMessage } from '@/lib/api-error';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { FileUpload } from '@/components/ui/file-upload';
import { RadioGroup, RadioGroupItemWithDescription } from '@/components/ui/radio-group-with-description';
import { FileListItem } from '@/components/analysis-form/file-list-item';
import { UploadProgressList } from '@/components/ui/upload-progress-list';
import { useUpload } from '@/lib/hooks/upload';
import { FileRole, startMultipleWorkflowsApiWorkflowsStartMultiplePost, WorkflowRunType } from '@/lib/generated-api';
import { toast } from 'sonner';
import { useQueryClient } from '@tanstack/react-query';

export interface FileUploadDialogProps {
  isOpen: boolean;
  title: string;
  description: string;
  multiple?: boolean;
  submitLabel?: string;
  projectId: string;
  /** Role assigned to the uploaded files. Defaults to supporting documents. */
  fileRole?: FileRole;
  /**
   * Let the user choose the file role (supporting document vs reviewer memo)
   * inside the dialog. When enabled, the chosen role drives both the upload
   * role and whether reference matching runs afterwards, overriding `fileRole`.
   * Not compatible with `referenceId`.
   */
  allowRoleSelection?: boolean;
  /** When set, force-matches the uploaded file to this reference instead of triggering the matching workflow. */
  referenceId?: string;
  onCancel: () => void;
  onComplete?: () => void;
}

export function FileUploadDialog({
  isOpen,
  title,
  description,
  multiple = false,
  submitLabel,
  projectId,
  fileRole = FileRole.Support,
  allowRoleSelection = false,
  referenceId,
  onCancel,
  onComplete,
}: FileUploadDialogProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedRole, setSelectedRole] = useState<FileRole>(fileRole);
  const [isStartingWorkflow, setIsStartingWorkflow] = useState(false);
  const queryClient = useQueryClient();
  const resetRef = useRef<(() => void) | null>(null);

  // When the user picks the role in-dialog, the selection drives the upload
  // role; otherwise the caller's `fileRole` prop is used.
  const activeRole = allowRoleSelection ? selectedRole : fileRole;
  const isMemoUpload = activeRole === FileRole.ReviewerMemo;
  // Reference matching only applies to supporting documents (that aren't
  // already tied to a specific reference); other roles skip it.
  const activeSkipMatching = activeRole !== FileRole.Support;
  const activeSuccessMessage = isMemoUpload ? 'Reviewer memos uploaded.' : 'Files uploaded. Matching workflow started.';

  const handleAllComplete = useCallback(async () => {
    if (referenceId) {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      toast.success('File uploaded and matched to reference.');
      onComplete?.();
      return;
    }

    if (activeSkipMatching) {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      toast.success(activeSuccessMessage);
      onComplete?.();
      return;
    }

    try {
      setIsStartingWorkflow(true);
      await startMultipleWorkflowsApiWorkflowsStartMultiplePost({
        body: {
          project_id: projectId,
          workflow_types: [WorkflowRunType.ReferenceFileMatching],
        },
      });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      toast.success(activeSuccessMessage);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to start file matching workflow'));
    } finally {
      setIsStartingWorkflow(false);
      onComplete?.();
    }
  }, [referenceId, activeSkipMatching, activeSuccessMessage, projectId, queryClient, onComplete]);

  const uploadHook = useUpload({
    projectId,
    fileRole: activeRole,
    referenceId,
    onAllComplete: handleAllComplete,
  });

  // Store reset in ref to avoid effect dependency on uploadHook
  resetRef.current = uploadHook.reset;

  // Reset state when dialog opens
  useEffect(() => {
    if (isOpen) {
      setSelectedFiles([]);
      setSelectedRole(fileRole);
      setIsStartingWorkflow(false);
      resetRef.current?.();
    }
  }, [isOpen, fileRole]);

  const handleFilesChange = (newFiles: File[]) => {
    setSelectedFiles(multiple ? newFiles : newFiles.slice(-1));
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleClose = useCallback(() => {
    setSelectedFiles([]);
    uploadHook.reset();
    onCancel();
  }, [onCancel, uploadHook]);

  const handleConfirm = async () => {
    if (selectedFiles.length === 0) return;
    uploadHook.startUpload(selectedFiles);
  };

  const canSubmit = selectedFiles.length > 0;

  const getSubmitLabel = () => {
    if (submitLabel) return submitLabel;
    if (multiple) {
      return `Upload ${selectedFiles.length} file${selectedFiles.length !== 1 ? 's' : ''}`;
    }
    return 'Upload';
  };

  const isUploading = uploadHook.isUploading || isStartingWorkflow;
  const allCompleted = uploadHook.completedCount > 0 && uploadHook.completedCount === uploadHook.totalCount;
  // Once files have been handed to the uploader we switch from the file-picker
  // view to the progress view. Both share the same dialog shell.
  const showProgress = uploadHook.files.length > 0;

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        // The progress view can't be dismissed by clicking outside or pressing
        // Escape; use its own controls (Cancel all / Done) instead.
        if (!open && !showProgress && !isUploading) handleClose();
      }}
    >
      <DialogContent
        className="sm:max-w-3xl max-h-[90vh] flex flex-col overflow-hidden"
        showCloseButton={!showProgress}
      >
        {showProgress ? (
          <>
            <DialogHeader className="flex-shrink-0">
              <DialogTitle>{isStartingWorkflow ? 'Starting file matching...' : 'Uploading files'}</DialogTitle>
              <DialogDescription>
                {isStartingWorkflow
                  ? 'Starting the file matching workflow to match uploaded files to references.'
                  : 'Your files are being uploaded. You can cancel at any time.'}
              </DialogDescription>
            </DialogHeader>

            <UploadProgressList
              files={uploadHook.files}
              overallProgress={uploadHook.overallProgress}
              completedCount={uploadHook.completedCount}
              totalCount={uploadHook.totalCount}
              onCancelFile={uploadHook.removeFile}
              onPauseFile={uploadHook.pauseFile}
              onResumeFile={uploadHook.resumeFile}
              onCancelAll={() => {
                uploadHook.cancelAll();
                handleClose();
              }}
              onPauseAll={uploadHook.pauseAll}
              onResumeAll={uploadHook.resumeAll}
              className="flex-1 min-h-0"
            />

            {allCompleted && !isStartingWorkflow && (
              <DialogFooter className="flex-shrink-0">
                <Button onClick={handleClose}>Done</Button>
              </DialogFooter>
            )}
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>{title}</DialogTitle>
              <DialogDescription>{description}</DialogDescription>
            </DialogHeader>

            <div className="space-y-4 flex-1 overflow-y-auto min-h-0">
              {allowRoleSelection && (
                <div className="space-y-2">
                  <Label>File type</Label>
                  <RadioGroup
                    value={selectedRole}
                    onValueChange={(v) => setSelectedRole(v as FileRole)}
                    className="grid grid-cols-2 gap-3"
                  >
                    <RadioGroupItemWithDescription
                      id={FileRole.Support}
                      value={selectedRole}
                      label="Supporting document"
                      description="Reference material cited by the document. Supporting files are matched against the document's references."
                      disabled={isUploading}
                    />
                    <RadioGroupItemWithDescription
                      id={FileRole.ReviewerMemo}
                      value={selectedRole}
                      label="Reviewer memo"
                      description="Peer-review feedback attached to the current revision. Used by the Peer Review Assistant assessments."
                      disabled={isUploading}
                    />
                  </RadioGroup>
                </div>
              )}
              <div className="space-y-2">
                <Label>{multiple ? 'Select Source Files' : 'Select Source File'}</Label>
                <FileUpload
                  files={selectedFiles}
                  onFilesChange={handleFilesChange}
                  accept=".pdf,.doc,.docx,.txt,.md"
                  multiple={multiple}
                  maxSize={500}
                  className="h-36"
                  disabled={isUploading}
                  compact
                />
              </div>

              {selectedFiles.length > 0 && (
                <div className="space-y-2">
                  <Label>{multiple ? `Selected Files (${selectedFiles.length})` : 'Selected File'}</Label>
                  <div className="space-y-1">
                    {selectedFiles.map((file, index) => (
                      <FileListItem
                        key={index}
                        file={file}
                        type={activeRole}
                        onRemove={() => handleRemoveFile(index)}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>

            <DialogFooter className="flex-shrink-0">
              <Button variant="outline" onClick={handleClose} disabled={isUploading}>
                Cancel
              </Button>
              <Button onClick={handleConfirm} disabled={!canSubmit || isUploading}>
                {getSubmitLabel()}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
