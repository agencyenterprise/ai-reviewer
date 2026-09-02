'use client';

import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { WorkflowConfigDialog, WorkflowConfigFormValues } from '@/components/workflows/workflow-config-dialog';
import { getErrorMessage } from '@/lib/api-error';
import { startMultipleWorkflowsApiWorkflowsStartMultiplePost } from '@/lib/generated-api';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { PlayIcon } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

/**
 * Starts assessments from the project header, so it is reachable from every
 * tab. Running one is the thing people come back to do, and burying it in the
 * Assessments tab made it a two-step trip from wherever they were reading.
 *
 * "Run", not "New": nothing is created here. The dialog is a multi-select over
 * the assessments that already exist, and every other control in this view
 * speaks the same way — "Ready to run", "Run more", "Re-run X".
 */
export function NewAssessmentButton({
  projectId,
  /** Off where the button is the only thing in its space and the label always fits. */
  collapseLabel = true,
}: {
  projectId: string;
  collapseLabel?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();

  const { mutate: startWorkflows } = useMutation({
    mutationFn: (values: WorkflowConfigFormValues) =>
      startMultipleWorkflowsApiWorkflowsStartMultiplePost({
        body: { project_id: projectId, workflow_types: values.workflowTypes },
      }),
    onSuccess: () => {
      toast.success('Assessments started');
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Failed to start assessments')),
  });

  return (
    <>
      <WorkflowConfigDialog
        isOpen={open}
        projectId={projectId}
        onConfirm={(values) => {
          setOpen(false);
          startWorkflows(values);
        }}
        onCancel={() => setOpen(false)}
      />

      <Tooltip>
        <TooltipTrigger asChild>
          <Button size="xs" onClick={() => setOpen(true)} aria-label="Run assessments">
            <PlayIcon />
            {/* A phone header cannot carry five labelled controls; here the
                icon and its tooltip say it instead. */}
            <span className={collapseLabel ? 'hidden sm:inline' : undefined}>Run assessments</span>
          </Button>
        </TooltipTrigger>
        <TooltipContent>Choose assessments to run on this document</TooltipContent>
      </Tooltip>
    </>
  );
}
