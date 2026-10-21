'use client';

import { Switch } from '@/components/ui/switch';
import { getErrorMessage } from '@/lib/api-error';
import { updateProjectEndpointApiProjectProjectIdPatch } from '@/lib/generated-api';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useWizard } from './wizard-context';

/**
 * Whether the new project shows its issues by severity. It opens on the value
 * the project inherited from the user's last one, and each change is saved to
 * the project straight away, so the next project inherits it in turn.
 */
export function GroupBySeveritySwitch({ disabled = false }: { disabled?: boolean }) {
  const { projectId, groupBySeverity, setGroupBySeverity } = useWizard();

  const save = useMutation({
    mutationFn: (value: boolean) => {
      if (!projectId) throw new Error('No project ID');
      return updateProjectEndpointApiProjectProjectIdPatch({
        path: { project_id: projectId },
        body: { group_by_severity: value },
      });
    },
    onMutate: (value) => setGroupBySeverity(value),
    onError: (error, value) => {
      setGroupBySeverity(!value);
      toast.error(getErrorMessage(error, 'Failed to save the severity setting'));
    },
  });

  return (
    <label className="flex cursor-pointer items-start gap-3 rounded-md border px-3 py-2.5">
      <Switch
        checked={groupBySeverity}
        onCheckedChange={(value) => save.mutate(value)}
        disabled={disabled || !projectId || save.isPending}
        className="mt-0.5"
      />
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-medium leading-tight">Group issues by severity</span>
        <span className="block text-xs text-muted-foreground">
          Turn off to list every issue with equal weight, here and in the Word export.
        </span>
      </span>
    </label>
  );
}
