'use client';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { WorkflowError } from '@/lib/generated-api';
import { isBlockingError } from '@/lib/workflow-state';
import { CopyIcon } from 'lucide-react';
import { toast } from 'sonner';

interface ErrorDetailsDialogProps {
  error: WorkflowError | null;
  onClose: () => void;
}

interface DetailSectionProps {
  title: string;
  hint?: string;
  content: string;
}

function DetailSection({ title, hint, content }: DetailSectionProps) {
  return (
    <section className="space-y-1.5">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
        {hint && <span className="ml-2 normal-case font-normal tracking-normal">{hint}</span>}
      </h4>
      <pre className="max-h-64 overflow-auto rounded-md bg-muted p-3 text-xs whitespace-pre-wrap break-words">
        {content}
      </pre>
    </section>
  );
}

/**
 * Everything recorded about one workflow error: the message, the exception
 * type, the failing model call's response metadata, the raw text the model
 * returned, and the traceback. Fields absent from older runs are omitted.
 */
export function ErrorDetailsDialog({ error, onClose }: ErrorDetailsDialogProps) {
  const details = error?.details;

  const copyToClipboard = async () => {
    if (!error) return;

    const sections = [
      `Task: ${error.task_name}`,
      details?.error_type && `Exception: ${details.error_type}`,
      `Message: ${error.error}`,
      error.workflow_run_id && `Workflow run: ${error.workflow_run_id}`,
      details?.llm_metadata && `\nModel response metadata:\n${JSON.stringify(details.llm_metadata, null, 2)}`,
      details?.raw_model_output && `\nRaw model output:\n${details.raw_model_output}`,
      details?.traceback && `\nTraceback:\n${details.traceback}`,
    ].filter(Boolean);

    try {
      await navigator.clipboard.writeText(sections.join('\n'));
      toast.success('Error details copied to clipboard');
    } catch {
      toast.error('Could not copy to the clipboard');
    }
  };

  return (
    <Dialog open={error !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-3xl">
        {error && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <span className="font-mono text-sm">{error.task_name}</span>
                <Badge variant={isBlockingError(error) ? 'destructive' : 'warning'}>
                  {isBlockingError(error) ? 'Error' : 'Warning'}
                </Badge>
                {details?.error_type && <Badge variant="outline">{details.error_type}</Badge>}
              </DialogTitle>
              <DialogDescription className="whitespace-pre-wrap break-words text-left">{error.error}</DialogDescription>
            </DialogHeader>

            <div className="space-y-4 overflow-y-auto max-h-[60vh] pr-1">
              {details?.llm_metadata && (
                <DetailSection
                  title="Model response metadata"
                  content={JSON.stringify(details.llm_metadata, null, 2)}
                />
              )}
              {details?.raw_model_output && (
                <DetailSection
                  title="Raw model output"
                  hint="what the model returned before the failure"
                  content={details.raw_model_output}
                />
              )}
              {details?.traceback && <DetailSection title="Traceback" content={details.traceback} />}
              {!details && (
                <p className="text-sm text-muted-foreground">
                  No diagnostics were recorded for this error. Runs from before diagnostics were captured store only the
                  message above.
                </p>
              )}
            </div>

            <DialogFooter className="sm:justify-between">
              <Button variant="outline" size="sm" onClick={copyToClipboard}>
                <CopyIcon className="w-4 h-4" />
                Copy details
              </Button>
              <Button size="sm" onClick={onClose}>
                Close
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
