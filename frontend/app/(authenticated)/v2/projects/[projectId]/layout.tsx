'use client';

import { useTabRouting } from '@/components/results/use-tab-routing';
import { AppBar } from '@/components/results-v2/app-bar';
import { ProjectShellV2 } from '@/components/results-v2/project-shell';
import { useProjectShellState } from '@/components/results-v2/use-project-shell-state';
import { isApiError } from '@/lib/api-error';
import { needsHumanApproval } from '@/lib/workflow-state';
import { FileXIcon, LockIcon } from 'lucide-react';
import { useParams } from 'next/navigation';
import { ReactNode } from 'react';

/** Centred panel for the states that exist before the project does. */
function StatusScreen({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-1 items-center justify-center p-8">
      <div className="max-w-sm text-center">{children}</div>
    </div>
  );
}

/**
 * The v2 tree mirrors the production project routes one level down, so
 * `/v2/projects/<id>/files` shows the same tab as `/projects/<id>/files` with the
 * redesigned chrome around it. Only the document explorer is redesigned so far;
 * the other tabs render their production panels unchanged.
 */
export default function ProjectLayoutV2({ children }: { children: ReactNode }) {
  const params = useParams();
  const projectId = params.projectId as string;

  const { activeTab, onTabChange } = useTabRouting(`/v2/projects/${projectId}`);

  const {
    project,
    workflowDetails,
    isLoading,
    error,
    effectiveRevision,
    handleRevisionChange,
    handleRevisionCreated,
    handleTitleSave,
    isTitleSaving,
    readOnly,
    isReadOnly,
    isViewingOldRevision,
  } = useProjectShellState(projectId);

  const statusScreen = isLoading ? (
    <StatusScreen>
      <div className="border-primary mx-auto mb-4 size-8 animate-spin rounded-full border-b-2" />
      <p className="text-muted-foreground">Loading project...</p>
    </StatusScreen>
  ) : isApiError(error, 403) ? (
    <StatusScreen>
      <LockIcon className="mx-auto mb-4 size-10 text-muted-foreground" />
      <h2 className="mb-2 text-lg font-semibold">Access denied</h2>
      <p className="text-sm text-muted-foreground">
        You don&apos;t have permission to view this project. Contact the project owner to request access.
      </p>
    </StatusScreen>
  ) : isApiError(error, 404) ? (
    <StatusScreen>
      <FileXIcon className="mx-auto mb-4 size-10 text-muted-foreground" />
      <h2 className="mb-2 text-lg font-semibold">Project not found</h2>
      <p className="text-sm text-muted-foreground">This project doesn&apos;t exist or may have been deleted.</p>
    </StatusScreen>
  ) : error ? (
    <StatusScreen>
      <p className="text-destructive">{error.message}</p>
    </StatusScreen>
  ) : !project ? (
    <StatusScreen>
      <p className="text-muted-foreground">Nothing to show.</p>
    </StatusScreen>
  ) : null;

  // The application row renders either way, so a slow load is never a blank page.
  if (statusScreen) {
    return (
      <div className="bg-background text-foreground flex h-dvh flex-col">
        <AppBar />
        {statusScreen}
      </div>
    );
  }

  return (
    <ProjectShellV2
      projectDetail={project!}
      activeTab={activeTab}
      onTabChange={onTabChange}
      readOnly={readOnly}
      onTitleSave={isReadOnly ? undefined : handleTitleSave}
      isTitleSaving={isReadOnly ? undefined : isTitleSaving}
      needsReferenceReview={!isReadOnly && !isViewingOldRevision && needsHumanApproval(workflowDetails)}
      selectedRevision={effectiveRevision}
      onRevisionChange={handleRevisionChange}
      onRevisionCreated={handleRevisionCreated}
    >
      {children}
    </ProjectShellV2>
  );
}
