import { getProjectWorkflowRunsByTypeEndpointApiProjectProjectIdWorkflowRunsGet } from '@/lib/generated-api';
import type { WorkflowRunDetail, WorkflowRunType } from '@/lib/generated-api';
import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

interface UseWorkflowSelectionParams {
  projectId: string;
  workflowDetails: WorkflowRunDetail[];
  shareToken?: string | null;
  /**
   * Shown until the reader picks one. Views that put the assessment list in a
   * rail pass the first entry, so the pane opens on something rather than on a
   * prompt to click the thing already in front of you.
   */
  defaultWorkflowType?: WorkflowRunType | null;
}

export function useWorkflowSelection({
  projectId,
  workflowDetails,
  shareToken,
  defaultWorkflowType = null,
}: UseWorkflowSelectionParams) {
  const [pickedWorkflowType, setPickedWorkflowType] = useState<WorkflowRunType | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  const selectedWorkflowType = pickedWorkflowType ?? defaultWorkflowType;

  const mainRequestWorkflow = selectedWorkflowType
    ? workflowDetails.find((w) => w.run.type === selectedWorkflowType)
    : null;

  // Query key includes main run info to auto-refetch when status/id changes
  const { data: historyData } = useQuery({
    queryKey: [
      'workflow-runs-history',
      projectId,
      selectedWorkflowType,
      mainRequestWorkflow?.run.id,
      mainRequestWorkflow?.run.status,
    ],
    queryFn: () =>
      getProjectWorkflowRunsByTypeEndpointApiProjectProjectIdWorkflowRunsGet({
        path: { project_id: projectId },
        query: { workflow_type: selectedWorkflowType!, share_token: shareToken },
      }),
    enabled: !!selectedWorkflowType,
    staleTime: 0,
  });

  const selectedWorkflowRun = useMemo(() => {
    if (!selectedWorkflowType) return null;

    if (historyData && historyData.length > 0) {
      if (selectedRunId) {
        const fromHistory = historyData.find((h) => h.run.id === selectedRunId);
        if (fromHistory) return fromHistory;
      }
      return historyData[0];
    }

    return mainRequestWorkflow ?? null;
  }, [selectedWorkflowType, selectedRunId, historyData, mainRequestWorkflow]);

  const handleSelectWorkflowType = (workflowType: WorkflowRunType) => {
    setPickedWorkflowType(workflowType);
    setSelectedRunId(null);
  };

  const handleSelectRun = (run: WorkflowRunDetail) => {
    setSelectedRunId(run.run.id);
  };

  return {
    selectedWorkflowType,
    selectedWorkflowRun,
    historyData,
    handleSelectWorkflowType,
    handleSelectRun,
  };
}
