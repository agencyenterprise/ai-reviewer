'use client';

import { useWorkflowProgressToast } from '@/hooks/use-workflow-progress-toast';
import { getErrorMessage } from '@/lib/api-error';
import { AccessLevel, ProjectDetailed, updateProjectEndpointApiProjectProjectIdPatch } from '@/lib/generated-api';
import { useProjectDetails } from '@/lib/hooks/use-project-details';
import { hasWorkflowProgressToShow } from '@/lib/workflow-state';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';
import { toast } from 'sonner';

/**
 * Everything the project chrome needs that is not chrome: the project itself,
 * which revision is being viewed, and saving the title.
 *
 * This mirrors the production `[projectId]/layout.tsx`, deliberately rather than
 * being shared with it — the v2 tree is meant to be deletable, and the
 * production layout should not have to care that it exists. Fold the two
 * together when v2 replaces it.
 */
export function useProjectShellState(projectId: string) {
  const queryClient = useQueryClient();

  // null means "follow the latest revision"
  const [selectedRevision, setSelectedRevision] = useState<number | null>(null);

  const { project, workflowDetails, isLoading, error } = useProjectDetails(projectId, selectedRevision);

  const currentRevision = project?.project?.current_revision ?? 1;
  const effectiveRevision = selectedRevision ?? currentRevision;

  const handleRevisionChange = useCallback((rev: number) => {
    setSelectedRevision(rev);
  }, []);

  // After a new revision is created, drop back to "follow latest" so the view and
  // switcher move to the newly created revision.
  const handleRevisionCreated = useCallback(() => {
    setSelectedRevision(null);
  }, []);

  // A pipeline parked on the reference-review gate isn't progressing — see
  // hasWorkflowProgressToShow.
  useWorkflowProgressToast(projectId, hasWorkflowProgressToShow(workflowDetails));

  const updateTitleMutation = useMutation({
    mutationFn: async (newTitle: string) => {
      return await updateProjectEndpointApiProjectProjectIdPatch({
        path: { project_id: projectId },
        body: { title: newTitle },
      });
    },
    onSuccess: (updatedProject) => {
      // The details query is keyed per revision (['project', id, revision]), so patch every
      // cached revision instead of an exact key that would never match.
      queryClient.setQueriesData({ queryKey: ['project', projectId] }, (curr: ProjectDetailed | undefined) =>
        curr ? { ...curr, project: updatedProject } : curr,
      );
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      toast.success('Title updated successfully');
    },
    onError: (mutationError) => {
      toast.error(`Failed to update title: ${getErrorMessage(mutationError, 'Unknown error')}`);
    },
  });

  const handleTitleSave = useCallback(
    async (newTitle: string) => {
      await updateTitleMutation.mutateAsync(newTitle);
    },
    [updateTitleMutation],
  );

  const isReadOnly = project ? project.access_level !== AccessLevel.Write : false;
  const isViewingOldRevision = effectiveRevision < currentRevision;

  return {
    project,
    workflowDetails,
    isLoading,
    error,
    effectiveRevision,
    handleRevisionChange,
    handleRevisionCreated,
    handleTitleSave,
    isTitleSaving: updateTitleMutation.isPending,
    readOnly: isReadOnly || isViewingOldRevision,
    isReadOnly,
    isViewingOldRevision,
  };
}
