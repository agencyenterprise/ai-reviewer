import { describe, expect, it } from 'vitest';
import { type ProjectOverview, WorkflowRunStatus, WorkflowRunType } from '@/lib/generated-api';
import { overviewRefetchInterval, projectQueryKeys } from './use-project-data';

function withRuns(...statuses: WorkflowRunStatus[]) {
  const data = {
    workflow_runs: statuses.map((status) => ({ run: { status }, errors: [] })),
  } as unknown as ProjectOverview;
  return { state: { data } };
}

describe('overviewRefetchInterval', () => {
  it('polls briskly while anything is working', () => {
    expect(overviewRefetchInterval(withRuns(WorkflowRunStatus.Completed, WorkflowRunStatus.Running))).toBe(3000);
    expect(overviewRefetchInterval(withRuns(WorkflowRunStatus.Pending))).toBe(3000);
  });

  it('polls slowly while a run waits on approval', () => {
    expect(overviewRefetchInterval(withRuns(WorkflowRunStatus.AwaitingApproval))).toBe(15000);
  });

  it('stops once nothing is left to change', () => {
    expect(overviewRefetchInterval(withRuns(WorkflowRunStatus.Completed, WorkflowRunStatus.Failed))).toBe(false);
    expect(overviewRefetchInterval({ state: {} })).toBe(false);
  });
});

describe('projectQueryKeys', () => {
  // Mutations invalidate `all(id)` and the issue resolution patches `allIssues(id)`:
  // a key that left those prefixes would silently stop refreshing.
  it('keeps every project-page query under the project prefix', () => {
    expect(projectQueryKeys.all('p')).toEqual(['project', 'p']);
    expect(projectQueryKeys.overviews('p')).toEqual(['project', 'p', 'overview']);
    expect(projectQueryKeys.overview('p', null)).toEqual(['project', 'p', 'overview', 'latest']);
    expect(projectQueryKeys.overview('p', 2)).toEqual(['project', 'p', 'overview', 2]);
    expect(projectQueryKeys.allIssues('p')).toEqual(['project', 'p', 'issues']);
    expect(projectQueryKeys.issues('p', 2)).toEqual(['project', 'p', 'issues', 2]);
    expect(projectQueryKeys.document('p', 2, 'v')).toEqual(['project', 'p', 'document', 2, 'v']);
    expect(projectQueryKeys.references('p', 2, 'v')).toEqual(['project', 'p', 'references', 2, 'v']);
    expect(projectQueryKeys.run('p', 'r', 'v')).toEqual(['project', 'p', 'run', 'r', 'v']);
    expect(projectQueryKeys.runHistory('p', WorkflowRunType.ReferenceValidationV2, 2, 'v')).toEqual([
      'project',
      'p',
      'run-history',
      WorkflowRunType.ReferenceValidationV2,
      2,
      'v',
    ]);
  });
});
