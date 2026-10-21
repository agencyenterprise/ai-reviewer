import { describe, expect, it } from 'vitest';
import { WorkflowRunPublic, WorkflowRunStatus, WorkflowRunType } from '@/lib/generated-api';
import { busyWorkflowTypes, runActivityLabel, runActivityStatus } from './run-activity-summary';
import { RunActivityItem } from './use-run-activity';

function item(currentStep = 0, totalSteps = 0): RunActivityItem {
  return { runId: crypto.randomUUID(), label: 'Abbreviation Scan', detail: null, currentStep, totalSteps };
}

function run(type: WorkflowRunType, status: WorkflowRunStatus): { run: WorkflowRunPublic } {
  return { run: { id: crypto.randomUUID(), type, status } as WorkflowRunPublic };
}

describe('runActivityLabel', () => {
  it('says the run is starting before any run is known', () => {
    expect(runActivityLabel({ running: [], queued: [] })).toBe('Starting…');
  });

  it('counts queued runs while none has started', () => {
    expect(runActivityLabel({ running: [], queued: [item(), item()] })).toBe('2 queued');
  });

  it("adds a single run's progress when it has steps to count", () => {
    expect(runActivityLabel({ running: [item(21, 50)], queued: [] })).toBe('Running · 42%');
    expect(runActivityLabel({ running: [item(0, 1)], queued: [] })).toBe('Running…');
  });

  it('counts several running assessments without blending their progress', () => {
    expect(runActivityLabel({ running: [item(1, 2), item(), item()], queued: [item()] })).toBe('Running 3…');
  });
});

describe('runActivityStatus', () => {
  it('names the running and queued counts', () => {
    expect(runActivityStatus({ running: [item(), item()], queued: [item()] })).toBe('2 assessments running, 1 queued');
    expect(runActivityStatus({ running: [], queued: [] })).toBe('Assessments starting');
  });

  it("carries a single run's visible progress", () => {
    expect(runActivityStatus({ running: [item(21, 50)], queued: [item()] })).toBe(
      'Abbreviation Scan 42% done, 1 queued',
    );
    expect(runActivityStatus({ running: [item(0, 1)], queued: [] })).toBe('1 assessment running');
  });
});

describe('busyWorkflowTypes', () => {
  it('holds running and queued assessments, not finished or waiting ones', () => {
    const runs = [
      run(WorkflowRunType.AbbreviationScanV2, WorkflowRunStatus.Running),
      run(WorkflowRunType.AdvocacyToneV2, WorkflowRunStatus.Pending),
      run(WorkflowRunType.FiguresTablesCheck, WorkflowRunStatus.Completed),
      run(WorkflowRunType.ReferenceValidationV2, WorkflowRunStatus.AwaitingApproval),
    ];
    expect(busyWorkflowTypes(runs)).toEqual([WorkflowRunType.AbbreviationScanV2, WorkflowRunType.AdvocacyToneV2]);
  });

  it('includes what was just started before the overview shows its runs', () => {
    expect(
      busyWorkflowTypes(
        [run(WorkflowRunType.AbbreviationScanV2, WorkflowRunStatus.Running)],
        [WorkflowRunType.AbbreviationScanV2, WorkflowRunType.Reviewer2],
      ).sort(),
    ).toEqual([WorkflowRunType.AbbreviationScanV2, WorkflowRunType.Reviewer2].sort());
  });
});
