'use client';

import { Button } from '@/components/ui/button';
import { Callout } from '@/components/ui/callout';
import { Tabs, TabsContent, TabsList } from '@/components/ui/tabs';
import { SimpleDeepAgentResults } from '@/components/workflows/results/simple-deep-agent-results';
import { FileRole, ProjectDetailed, WorkflowRunDetail, WorkflowRunStatus, WorkflowRunType } from '@/lib/generated-api';
import { getDisplayStatus } from '@/lib/workflow-state';
import { ClipboardCheck, History, ListChecks, MessagesSquare, Upload } from 'lucide-react';
import { useState } from 'react';
import { ReplaceMainDocumentDialog } from '../../components/replace-main-document-dialog';
import { FileUploadDialog } from '../reference-review/file-upload-dialog';
import { PeerReviewEmptyState } from './peer-review-empty-state';
import { PeerReviewMemosCard } from './peer-review-memos-card';
import {
  PeerReviewStageAction,
  PeerReviewStageCta,
  PeerReviewStagePanel,
  PeerReviewStepTrigger,
} from './peer-review-stage-card';
import { usePeerReviewState } from './use-peer-review-state';

type StageId = 'plan' | 'revise' | 'respond' | 'coverage';

interface PeerReviewTabProps {
  projectDetail: ProjectDetailed;
  readOnly?: boolean;
  onRevisionChange?: (revision: number) => void;
  onRevisionCreated?: () => void;
  onNavigateToDocumentExplorer: (lineRange?: [number, number]) => void;
}

const isComplete = (run?: WorkflowRunDetail) => !!run && getDisplayStatus(run) === WorkflowRunStatus.Completed;

export function PeerReviewTab({
  projectDetail,
  readOnly = false,
  onRevisionChange,
  onRevisionCreated,
  onNavigateToDocumentExplorer,
}: PeerReviewTabProps) {
  const { facts, planFallback, startStage, cancelRun, isStarting } = usePeerReviewState({ projectDetail });
  const [isMemoUploadOpen, setIsMemoUploadOpen] = useState(false);
  const [isRevisionDialogOpen, setIsRevisionDialogOpen] = useState(false);

  const { runs, currentRevision, reviewedRevision, hasRevisedDraft, isViewingOldRevision } = facts;

  // The plan for the reviewed draft stays relevant after a new revision exists,
  // so fall back to the run on that revision rather than showing step 1 empty.
  const planRun = runs.plan ?? planFallback?.run;
  const planRunRevision = runs.plan ? facts.viewedRevision : planFallback?.revision;
  const planRunProject = runs.plan ? projectDetail : (planFallback?.projectDetail ?? projectDetail);
  const planComplete = isComplete(planRun);
  const memosComplete = isComplete(runs.memos);
  const coverageComplete = isComplete(runs.coverage);

  // Land on the furthest step that has something to show. Held in state rather
  // than recomputed, so the 3s project poll cannot move the selection out from
  // under someone who is reading.
  const [activeStage, setActiveStage] = useState<StageId>(() => {
    if (runs.coverage) return 'coverage';
    if (runs.memos || hasRevisedDraft) return 'respond';
    if (planComplete) return 'revise';
    return 'plan';
  });

  const memoDialog = (
    <FileUploadDialog
      isOpen={isMemoUploadOpen}
      projectId={projectDetail.project.id}
      title="Upload reviewer memos"
      description="Add the memos your peer reviewers returned. They are read against the draft the reviewers saw."
      multiple
      fileRole={FileRole.ReviewerMemo}
      allowRevisionSelection
      currentRevision={currentRevision}
      onCancel={() => setIsMemoUploadOpen(false)}
      onComplete={() => setIsMemoUploadOpen(false)}
    />
  );

  if (reviewedRevision === null) {
    return (
      <div className="space-y-4">
        <PeerReviewHeader />
        <PeerReviewEmptyState readOnly={readOnly} onUploadMemos={() => setIsMemoUploadOpen(true)} />
        {memoDialog}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <PeerReviewHeader />

      {isViewingOldRevision && (
        <Callout variant="info" icon={History} title={`Viewing revision ${facts.viewedRevision}`}>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm min-w-0">
              These assessments always run against the current draft, revision {currentRevision}.
            </p>
            {onRevisionChange && (
              <Button
                size="sm"
                variant="outline"
                className="shrink-0"
                onClick={() => onRevisionChange(currentRevision)}
              >
                View current
              </Button>
            )}
          </div>
        </Callout>
      )}

      <PeerReviewMemosCard
        facts={facts}
        projectId={projectDetail.project.id}
        readOnly={readOnly}
        onUploadMemos={() => setIsMemoUploadOpen(true)}
      />

      <Tabs value={activeStage} onValueChange={(value) => setActiveStage(value as StageId)} className="gap-4">
        <TabsList className="grid h-auto w-full grid-cols-1 gap-3 bg-transparent p-0 sm:grid-cols-2 xl:grid-cols-4">
          <PeerReviewStepTrigger
            value="plan"
            index={1}
            title="Plan the revision"
            subtitle="Every reviewer point, located and actionable."
            complete={planComplete}
            blocked={facts.planBlockedReason !== null}
            run={planRun}
          />
          <PeerReviewStepTrigger
            value="revise"
            index={2}
            title="Upload your revised draft"
            subtitle="Creates the revision the response compares against."
            complete={hasRevisedDraft}
            blocked={facts.reviseBlockedReason !== null}
            readyLabel="Ready to upload"
          />
          <PeerReviewStepTrigger
            value="respond"
            index={3}
            title="Respond to the reviewers"
            subtitle="One response memo per reviewer, point by point."
            complete={memosComplete}
            blocked={facts.comparisonBlockedReason !== null}
            run={runs.memos}
          />
          <PeerReviewStepTrigger
            value="coverage"
            index={4}
            title="QA coverage report"
            subtitle="A verdict per point, consolidated for a QA manager."
            complete={coverageComplete}
            blocked={facts.comparisonBlockedReason !== null}
            run={runs.coverage}
          />
        </TabsList>

        <TabsContent value="plan">
          <PeerReviewStagePanel
            blockedReason={facts.planBlockedReason}
            actions={
              planRun &&
              !readOnly && (
                <PeerReviewStageAction
                  label="Generate planning summary"
                  reRunLabel={planFallback ? `Generate again for revision ${currentRevision}` : undefined}
                  run={planRun}
                  disabled={facts.planBlockedReason !== null}
                  isStarting={isStarting}
                  onStart={() => startStage([WorkflowRunType.RevisionPlanningSummary])}
                  onCancel={cancelRun}
                />
              )
            }
          >
            {planRun ? (
              <div className="space-y-3">
                <p className="text-xs text-muted-foreground">
                  Based on revision {planRunRevision} — the draft your reviewers read, and the{' '}
                  {facts.activeMemos.length} memo{facts.activeMemos.length === 1 ? '' : 's'} attached to it.
                  {planFallback && ' It still applies: those memos have not changed.'}
                </p>
                <SimpleDeepAgentResults
                  project={planRunProject}
                  workflowDetail={planRun}
                  workflowName="Revision-Planning Summary"
                  onNavigateToDocumentExplorer={onNavigateToDocumentExplorer}
                />
              </div>
            ) : (
              <PeerReviewStageCta
                icon={ListChecks}
                title="Turn the reviewers' memos into a revision plan"
                description={`Reads the ${facts.activeMemos.length} memo${facts.activeMemos.length === 1 ? '' : 's'} on revision ${reviewedRevision} against that revision's draft, reproduces each memo verbatim, and adds a planning note under every point.`}
                action={
                  !readOnly && (
                    <PeerReviewStageAction
                      label="Generate planning summary"
                      run={undefined}
                      disabled={facts.planBlockedReason !== null}
                      isStarting={isStarting}
                      size="default"
                      onStart={() => startStage([WorkflowRunType.RevisionPlanningSummary])}
                      onCancel={cancelRun}
                    />
                  )
                }
              />
            )}
          </PeerReviewStagePanel>
        </TabsContent>

        <TabsContent value="revise">
          <PeerReviewStagePanel
            blockedReason={facts.reviseBlockedReason}
            actions={
              hasRevisedDraft &&
              !readOnly && (
                <Button variant="outline" size="sm" onClick={() => setIsRevisionDialogOpen(true)}>
                  <Upload className="size-4" />
                  Create another revision
                </Button>
              )
            }
          >
            {hasRevisedDraft ? (
              <p className="text-sm text-muted-foreground">
                Revision {currentRevision} is your revised draft. Revision {reviewedRevision} is kept as the draft the
                reviewers read, and steps 3 and 4 compare the two.
              </p>
            ) : (
              <PeerReviewStageCta
                icon={Upload}
                title="Upload the draft you revised"
                description={`Revision ${reviewedRevision} is the draft your reviewers read. Uploading your revised version creates a new revision — revision ${reviewedRevision} and all its results are kept, and steps 3 and 4 compare the two.`}
                action={
                  !readOnly && (
                    <Button disabled={facts.reviseBlockedReason !== null} onClick={() => setIsRevisionDialogOpen(true)}>
                      <Upload className="size-4" />
                      Upload revised draft
                    </Button>
                  )
                }
              />
            )}
          </PeerReviewStagePanel>
        </TabsContent>

        <TabsContent value="respond">
          <PeerReviewStagePanel
            blockedReason={facts.comparisonBlockedReason}
            actions={
              runs.memos &&
              !readOnly && (
                <PeerReviewStageAction
                  label="Generate response memos"
                  run={runs.memos}
                  disabled={facts.comparisonBlockedReason !== null}
                  isStarting={isStarting}
                  onStart={() => startStage([WorkflowRunType.ReviewerResponseMemos])}
                  onCancel={cancelRun}
                />
              )
            }
          >
            {runs.memos ? (
              <SimpleDeepAgentResults
                project={projectDetail}
                workflowDetail={runs.memos}
                workflowName="Reviewer Response Memos"
                onNavigateToDocumentExplorer={onNavigateToDocumentExplorer}
              />
            ) : (
              <PeerReviewStageCta
                icon={MessagesSquare}
                title="Draft a reply to every reviewer point"
                description={`One response memo per reviewer. Compares revision ${currentRevision} against revision ${reviewedRevision} to state, for every point, what changed and where, or why it was not changed.`}
                action={
                  !readOnly && (
                    <PeerReviewStageAction
                      label="Generate response memos"
                      run={undefined}
                      disabled={facts.comparisonBlockedReason !== null}
                      isStarting={isStarting}
                      size="default"
                      onStart={() => startStage([WorkflowRunType.ReviewerResponseMemos])}
                      onCancel={cancelRun}
                    />
                  )
                }
              />
            )}
          </PeerReviewStagePanel>
        </TabsContent>

        <TabsContent value="coverage">
          <PeerReviewStagePanel
            blockedReason={facts.comparisonBlockedReason}
            actions={
              runs.coverage &&
              !readOnly && (
                <PeerReviewStageAction
                  label="Generate coverage report"
                  run={runs.coverage}
                  disabled={facts.comparisonBlockedReason !== null}
                  isStarting={isStarting}
                  onStart={() => startStage([WorkflowRunType.ReviewerCoverageReport])}
                  onCancel={cancelRun}
                />
              )
            }
          >
            {runs.coverage ? (
              <SimpleDeepAgentResults
                project={projectDetail}
                workflowDetail={runs.coverage}
                workflowName="Reviewer Coverage Report"
                onNavigateToDocumentExplorer={onNavigateToDocumentExplorer}
              />
            ) : (
              <PeerReviewStageCta
                icon={ClipboardCheck}
                title="Sign off on how responsive the revision was"
                description="A single view for a QA manager: every reviewer point with a verdict (addressed, partially addressed, declined with rationale, or not addressed), a summary count table, and an overall responsiveness read."
                action={
                  !readOnly && (
                    <PeerReviewStageAction
                      label="Generate coverage report"
                      run={undefined}
                      disabled={facts.comparisonBlockedReason !== null}
                      isStarting={isStarting}
                      size="default"
                      onStart={() => startStage([WorkflowRunType.ReviewerCoverageReport])}
                      onCancel={cancelRun}
                    />
                  )
                }
              />
            )}
          </PeerReviewStagePanel>
        </TabsContent>
      </Tabs>

      {memoDialog}
      <ReplaceMainDocumentDialog
        isOpen={isRevisionDialogOpen}
        projectId={projectDetail.project.id}
        onClose={() => setIsRevisionDialogOpen(false)}
        onRevisionCreated={onRevisionCreated}
        hideRerunOption
      />
    </div>
  );
}

function PeerReviewHeader() {
  return (
    <div className="space-y-1">
      <h2 className="text-lg font-semibold">Peer review</h2>
      <p className="text-sm text-muted-foreground">
        Plan your revision from the reviewers&apos; memos, upload the revised draft, then generate the response memos
        and the coverage report.
      </p>
    </div>
  );
}
