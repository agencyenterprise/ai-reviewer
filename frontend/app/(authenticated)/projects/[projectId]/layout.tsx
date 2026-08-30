'use client';

import { ProjectResultsShell } from '@/components/results/project-results-shell';
import { useTabRouting } from '@/components/results/use-tab-routing';
import { useWorkflowProgressToast } from '@/hooks/use-workflow-progress-toast';
import { getErrorMessage, isApiError } from '@/lib/api-error';
import { AccessLevel, ProjectDetailed, updateProjectEndpointApiProjectProjectIdPatch } from '@/lib/generated-api';
import { useProjectDetails } from '@/lib/hooks/use-project-details';
import { isAnyWorkflowProcessing, needsHumanApproval } from '@/lib/workflow-state';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { FileXIcon, LockIcon } from 'lucide-react';
import { useParams } from 'next/navigation';
import { ReactNode, useCallback, useState } from 'react';
import { toast } from 'sonner';

export default function ProjectLayout({ children }: { children: ReactNode }) {
  const params = useParams();
  const projectId = params.projectId as string;
  const queryClient = useQueryClient();

  const { activeTab, onTabChange } = useTabRouting(`/projects/${projectId}`);

  // Revision state: null means "latest" (default)
  const [selectedRevision, setSelectedRevision] = useState<number | null>(null);

  const { project, workflowDetails, isLoading, error } = useProjectDetails(projectId, selectedRevision);

  // When project loads and we haven't selected a revision yet, sync to current
  const currentRevision = project?.project?.current_revision ?? 1;
  const effectiveRevision = selectedRevision ?? currentRevision;

  const handleRevisionChange = useCallback((rev: number) => {
    setSelectedRevision(rev);
  }, []);

  // After a new revision is created, drop back to "follow latest" so the view
  // and switcher move to the newly created (now current) revision instead of
  // staying pinned to the previously selected one.
  const handleRevisionCreated = useCallback(() => {
    setSelectedRevision(null);
  }, []);

  const isProcessing = isAnyWorkflowProcessing(workflowDetails);
  const awaitingHumanApproval = needsHumanApproval(workflowDetails);
  // HumanApproval stays Pending/Running until the user approves, which keeps isProcessing true even though
  // the pipeline is intentionally paused. The progress API then has no active step → "Going to next step...".
  const showWorkflowProgressToast = isProcessing && !awaitingHumanApproval;

  // Show progress in toast when automated workflows are running (not while waiting on reference review / approve)
  useWorkflowProgressToast(projectId, showWorkflowProgressToast);

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
      queryClient.setQueriesData({ queryKey: ['project', projectId] }, (curr: ProjectDetailed | undefined) => {
        if (!curr) return curr;
        return {
          ...curr,
          project: updatedProject,
        };
      });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      toast.success('Title updated successfully');
    },
    onError: (error) => {
      toast.error(`Failed to update title: ${getErrorMessage(error, 'Unknown error')}`);
    },
  });

  const handleTitleSave = async (newTitle: string) => {
    await updateTitleMutation.mutateAsync(newTitle);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading project...</p>
        </div>
      </div>
    );
  }

  if (isApiError(error, 403)) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center max-w-sm">
          <LockIcon className="h-10 w-10 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-lg font-semibold mb-2">Access Denied</h2>
          <p className="text-muted-foreground text-sm">
            You don&apos;t have permission to view this project. Contact the project owner to request access.
          </p>
        </div>
      </div>
    );
  }

  if (isApiError(error, 404)) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center max-w-sm">
          <FileXIcon className="h-10 w-10 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-lg font-semibold mb-2">Project Not Found</h2>
          <p className="text-muted-foreground text-sm">This project doesn&apos;t exist or may have been deleted.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center">
        <div className="text-center">
          <p className="text-destructive mb-4">{error.message}</p>
        </div>
      </div>
    );
  }

  if (!project) {
    return null;
  }

  const isReadOnly = project.access_level !== AccessLevel.Write;

  const isViewingOldRevision = effectiveRevision < currentRevision;

  return (
    <ProjectResultsShell
      projectDetail={project}
      activeTab={activeTab}
      onTabChange={onTabChange}
      readOnly={isReadOnly || isViewingOldRevision}
      onTitleSave={isReadOnly ? undefined : handleTitleSave}
      isTitleSaving={isReadOnly ? undefined : updateTitleMutation.isPending}
      needsReferenceReview={!isReadOnly && !isViewingOldRevision && needsHumanApproval(workflowDetails)}
      selectedRevision={effectiveRevision}
      onRevisionChange={handleRevisionChange}
      onRevisionCreated={handleRevisionCreated}
    >
      {children}
    </ProjectResultsShell>
  );
}
