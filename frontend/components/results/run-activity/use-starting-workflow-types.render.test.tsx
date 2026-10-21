import { useMutation } from '@tanstack/react-query';
import { act } from 'react';
import { afterEach, describe, expect, it } from 'vitest';
import { WorkflowRunType } from '@/lib/generated-api';
import { flush, renderInto, testQueryClient, withQueryClient, type Rendered } from '@/lib/test-render';
import { startAssessmentsKey, useStartingWorkflowTypes } from './use-starting-workflow-types';

const PROJECT = 'project-1';

let rendered: Rendered | undefined;
afterEach(async () => {
  await rendered?.unmount();
  rendered = undefined;
});

/** Starts batches that stay in flight until the test resolves them. */
async function mountHarness() {
  const pending: Array<() => void> = [];
  const seen: { types: WorkflowRunType[]; start?: (types: WorkflowRunType[]) => void } = { types: [] };

  function Harness() {
    const { mutate } = useMutation<void, Error, { workflowTypes: WorkflowRunType[] }>({
      mutationKey: startAssessmentsKey(PROJECT),
      mutationFn: () => new Promise<void>((resolve) => pending.push(resolve)),
    });
    seen.types = useStartingWorkflowTypes(PROJECT);
    seen.start = (types) => mutate({ workflowTypes: types });
    return null;
  }

  rendered = await renderInto(withQueryClient(testQueryClient(), <Harness />));
  return { seen, pending };
}

describe('useStartingWorkflowTypes', () => {
  it('keeps an earlier batch while a later one is also in flight', async () => {
    const { seen, pending } = await mountHarness();

    await act(async () => seen.start!([WorkflowRunType.AbbreviationScanV2]));
    await act(async () => seen.start!([WorkflowRunType.Reviewer2]));
    await flush();

    expect(seen.types.sort()).toEqual([WorkflowRunType.AbbreviationScanV2, WorkflowRunType.Reviewer2].sort());

    // The first batch landing leaves only the second one starting.
    await act(async () => pending[0]());
    await flush();
    expect(seen.types).toEqual([WorkflowRunType.Reviewer2]);
  });
});
