'use client';

import { Callout } from '@/components/ui/callout';
import { ErrorsCard } from '@/components/results/components/errors-card';
import { GenericWorkflowResults } from '@/components/results/components/generic-workflow-results';
import { AboutThisGerResults } from '@/components/workflows/results/about-this-ger-results';
import { AdvocacyToneResults } from '@/components/workflows/results/advocacy-tone-results';
import { CitationSuggesterResults } from '@/components/workflows/results/citation-suggester-results';
import { LiteratureReviewResults } from '@/components/workflows/results/literature-review/literature-review-results';
import { LiveReportsResults } from '@/components/workflows/results/live-reports-results';
import { MethodologicalAlignmentResults } from '@/components/workflows/results/methodological-alignment-results';
import { ReferenceDownloaderResults } from '@/components/workflows/results/reference-downloader-results';
import { ReferenceValidationResults } from '@/components/workflows/results/reference-validation-results';
import { ReferenceValidationV2Results } from '@/components/workflows/results/reference-validation-v2-results';
import { ResultsExtractorResults } from '@/components/workflows/results/results-extractor-results';
import { Reviewer2Results } from '@/components/workflows/results/reviewer-2-results';
import { SimpleDeepAgentResults } from '@/components/workflows/results/simple-deep-agent-results';
import { ProjectDetailed, SimpleDeepAgentState, WorkflowRunDetail, WorkflowRunType } from '@/lib/generated-api';
import { useWorkflowTypes } from '@/lib/hooks/use-workflow-types';
import { getCurrentRunErrors, WorkflowRunDetailTyped } from '@/lib/workflow-state';
import { FlaskConicalIcon } from 'lucide-react';

function InternalWorkflowResults({ workflowName }: { workflowName: string }) {
  return (
    <Callout title="Internal Workflow" variant="info" icon={FlaskConicalIcon}>
      <p className="text-sm">
        <strong>{workflowName}</strong> runs automatically as a dependency of other assessments and is not meant to be
        triggered directly — its results feed into higher-level workflows that surface findings in their own result
        views.
      </p>
    </Callout>
  );
}

interface WorkflowResultsContentProps {
  projectDetail: ProjectDetailed;
  workflowRun: WorkflowRunDetail;
  onNavigateToDocumentExplorer: (lineRange?: [number, number]) => void;
  onNavigateToReferences: () => void;
}

function renderWorkflowResults(
  project: ProjectDetailed,
  workflowRun: WorkflowRunDetail,
  onNavigateToDocumentExplorer: (lineRange?: [number, number]) => void,
  getWorkflowTypeName: (type: WorkflowRunType) => string,
) {
  const { type } = workflowRun.run;
  const { state } = workflowRun;

  if (!state) {
    return <div className="p-4 text-center text-muted-foreground">No results available for this workflow run</div>;
  }

  switch (type) {
    case WorkflowRunType.MethodologicalAlignment:
      return <MethodologicalAlignmentResults workflowDetail={workflowRun} />;
    case WorkflowRunType.LiveReports:
      return <LiveReportsResults project={project} workflowDetail={workflowRun} />;
    case WorkflowRunType.LiteratureReview:
      return <LiteratureReviewResults workflowDetail={workflowRun} />;
    case WorkflowRunType.CitationSuggester:
      return <CitationSuggesterResults project={project} />;
    case WorkflowRunType.ReferenceDownloader:
      return <ReferenceDownloaderResults workflowDetail={workflowRun} />;
    case WorkflowRunType.ResultsExtraction:
      return <ResultsExtractorResults workflowDetail={workflowRun} />;
    case WorkflowRunType.AdvocacyTone:
      return <AdvocacyToneResults project={project} onNavigateToDocumentExplorer={onNavigateToDocumentExplorer} />;
    case WorkflowRunType.AboutThisGer:
      return <AboutThisGerResults workflowDetail={workflowRun} />;
    case WorkflowRunType.ClaimReferenceValidation:
    case WorkflowRunType.ClaimReferenceValidationV2:
    case WorkflowRunType.AbbreviationScanV2:
      return (
        <GenericWorkflowResults
          project={project}
          workflowRun={workflowRun}
          workflowName={getWorkflowTypeName(type)}
          onNavigateToDocumentExplorer={onNavigateToDocumentExplorer}
        />
      );
    case WorkflowRunType.Reviewer2:
      return <Reviewer2Results workflowDetail={workflowRun} />;
    case WorkflowRunType.ReferenceValidation:
      return <ReferenceValidationResults workflowDetail={workflowRun} />;
    case WorkflowRunType.ReferenceValidationV2:
      return <ReferenceValidationV2Results workflowDetail={workflowRun} />;
    case WorkflowRunType.DocumentStructure:
    case WorkflowRunType.FiguresTablesCheck:
    case WorkflowRunType.InferenceValidationV2:
    case WorkflowRunType.RecommendationCheck:
    case WorkflowRunType.RevisionPlanningSummary:
    case WorkflowRunType.ReviewerResponseMemos:
    case WorkflowRunType.ReviewerCoverageReport:
    case WorkflowRunType.AdvocacyToneV2:
    case WorkflowRunType.LiteratureReviewV2:
    case WorkflowRunType.LiveReportsV2:
      return (
        <SimpleDeepAgentResults
          project={project}
          workflowDetail={workflowRun as WorkflowRunDetailTyped<SimpleDeepAgentState>}
          workflowName={getWorkflowTypeName(type)}
          onNavigateToDocumentExplorer={onNavigateToDocumentExplorer}
        />
      );
    default:
      // No bespoke visualisation for this type: fall back to its issues, which
      // every assessment produces, rather than telling the user nothing.
      return (
        <GenericWorkflowResults
          project={project}
          workflowRun={workflowRun}
          workflowName={getWorkflowTypeName(type)}
          onNavigateToDocumentExplorer={onNavigateToDocumentExplorer}
        />
      );
  }
}

export function WorkflowResultsContent({
  projectDetail,
  workflowRun,
  onNavigateToDocumentExplorer,
}: WorkflowResultsContentProps) {
  const currentErrors = getCurrentRunErrors(workflowRun);
  const { getWorkflowTypeName, isWorkflowTypeVisible } = useWorkflowTypes();
  const workflowName = getWorkflowTypeName(workflowRun.run.type);

  if (!isWorkflowTypeVisible(workflowRun.run.type)) {
    return (
      <>
        {currentErrors.length > 0 && <ErrorsCard errors={currentErrors} />}
        <InternalWorkflowResults workflowName={workflowName} />
      </>
    );
  }

  return (
    <>
      {currentErrors.length > 0 && <ErrorsCard errors={currentErrors} />}
      {renderWorkflowResults(projectDetail, workflowRun, onNavigateToDocumentExplorer, getWorkflowTypeName)}
    </>
  );
}
