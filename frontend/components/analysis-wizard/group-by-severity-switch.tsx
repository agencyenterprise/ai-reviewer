'use client';

import { Switch } from '@/components/ui/switch';
import { getErrorMessage } from '@/lib/api-error';
import { updateProjectEndpointApiProjectProjectIdPatch } from '@/lib/generated-api';
import { projectQueryKeys } from '@/lib/hooks/use-project-data';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useWizard } from './wizard-context';

/**
 * Saves the new project's severity setting the moment it changes, so the next
 * project inherits it in turn. The step holds Start and Skip while a save is in
 * flight: leaving before it lands would open the project on the old value.
 */
export function useSaveGroupBySeverity() {
  const { projectId, setGroupBySeverity } = useWizard();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (value: boolean) => {
      if (!projectId) throw new Error('No project ID');
      return updateProjectEndpointApiProjectProjectIdPatch({
        path: { project_id: projectId },
        body: { group_by_severity: value },
      });
    },
    onMutate: (value) => setGroupBySeverity(value),
    onSuccess: () => {
      if (projectId) queryClient.invalidateQueries({ queryKey: projectQueryKeys.overviews(projectId) });
    },
    onError: (error, value) => {
      setGroupBySeverity(!value);
      toast.error(getErrorMessage(error, 'Failed to save the severity setting'));
    },
  });
}

interface GroupBySeveritySwitchProps {
  checked: boolean;
  onCheckedChange: (value: boolean) => void;
  disabled?: boolean;
}

/** Whether the new project shows its issues by severity; it opens on the value inherited from the last project. */
export function GroupBySeveritySwitch({ checked, onCheckedChange, disabled = false }: GroupBySeveritySwitchProps) {
  return (
    <label className="flex cursor-pointer items-start gap-3 rounded-md border px-3 py-2.5">
      <Switch checked={checked} onCheckedChange={onCheckedChange} disabled={disabled} className="mt-0.5" />
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-medium leading-tight">Group issues by severity</span>
        <span className="block text-xs text-muted-foreground">
          Turn off to list every issue with equal weight, here and in the Word export. You can change this later from
          Edit Project in the project menu.
        </span>
      </span>
    </label>
  );
}
