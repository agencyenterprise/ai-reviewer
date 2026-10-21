import { act } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { WorkflowRunType, type WorkflowTypeDescription } from '@/lib/generated-api';
import { renderInto, type Rendered } from '@/lib/test-render';
import { WorkflowTypeSelector } from './workflow-type-selector';

function workflowType(type: WorkflowRunType, name: string): WorkflowTypeDescription {
  return {
    type,
    name,
    description: `${name} description`,
    needs_web_search: false,
    is_experimental: false,
    is_internal: false,
    category: 'language',
    gates: [],
  };
}

const TYPES = [
  workflowType(WorkflowRunType.AbbreviationScanV2, 'Abbreviations'),
  workflowType(WorkflowRunType.AdvocacyToneV2, 'Advocacy Tone'),
  workflowType(WorkflowRunType.FiguresTablesCheck, 'Figures and Tables'),
];

vi.mock('@/lib/hooks/use-workflow-types', () => ({
  useWorkflowTypes: () => ({ workflowTypes: TYPES, getWorkflowTypeName: (t: string) => t, isPending: false }),
}));
vi.mock('@/lib/hooks/use-workflow-duration-estimates', () => ({
  useWorkflowDurationEstimates: () => ({ getEstimatedSeconds: () => null }),
}));
vi.mock('@/lib/hooks/use-visible-workflow-types', () => ({
  useVisibleWorkflowTypes: () => ({
    visibleGroups: [{ category: { slug: 'language', label: 'Language' }, workflows: TYPES }],
    presets: [],
  }),
}));

let rendered: Rendered | undefined;
afterEach(async () => {
  await rendered?.unmount();
  rendered = undefined;
});

async function mount(selectedTypes: WorkflowRunType[], runningTypes: WorkflowRunType[]) {
  const onSelectionChange = vi.fn();
  rendered = await renderInto(
    <WorkflowTypeSelector
      selectedTypes={selectedTypes}
      onSelectionChange={onSelectionChange}
      runningTypes={runningTypes}
    />,
  );
  const checkbox = (type: WorkflowRunType) => rendered!.container.querySelector<HTMLButtonElement>(`[id="${type}"]`)!;
  const button = (label: string) =>
    Array.from(rendered!.container.querySelectorAll('button')).find((b) => b.textContent === label)!;
  return { onSelectionChange, checkbox, button };
}

describe('WorkflowTypeSelector with running assessments', () => {
  it('locks running assessments out of the selection', async () => {
    const { checkbox } = await mount([WorkflowRunType.AbbreviationScanV2], [WorkflowRunType.AbbreviationScanV2]);

    expect(checkbox(WorkflowRunType.AbbreviationScanV2).disabled).toBe(true);
    // Ticked before it started elsewhere, it no longer reads as selected.
    expect(checkbox(WorkflowRunType.AbbreviationScanV2).getAttribute('data-state')).toBe('unchecked');
    expect(checkbox(WorkflowRunType.AdvocacyToneV2).disabled).toBe(false);
  });

  it('leaves running assessments out of Select all', async () => {
    const { onSelectionChange, button } = await mount([], [WorkflowRunType.AdvocacyToneV2]);

    await act(async () => button('Select all').click());

    expect(onSelectionChange).toHaveBeenCalledWith([
      WorkflowRunType.AbbreviationScanV2,
      WorkflowRunType.FiguresTablesCheck,
    ]);
  });
});
