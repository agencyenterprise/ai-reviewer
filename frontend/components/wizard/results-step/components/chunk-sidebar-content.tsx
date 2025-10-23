import { ChunkReevaluationResponse, ClaimSubstantiatorStateOutput } from '@/lib/generated-api';
import { ChunkAnalysisCard } from './chunk-analysis-card';
import { ChunkEvalGenerator } from './chunk-eval-generator';
import { ChunkReevaluateControl } from './chunk-reevaluate-control';
import { ChunkStatusBadge, useShouldShowStatusBadge } from './chunk-status-badge';
import { ClaimAnalysisCard } from './claim-analysis-card';
import { ErrorsCard } from './errors-card';

export interface ChunkSidebarContentProps {
  results: ClaimSubstantiatorStateOutput;
  chunkIndex: number | null;
  isWorkflowRunning: boolean;
  onChunkReevaluation: (response: ChunkReevaluationResponse) => void;
}

export function ChunkSidebarContent({
  results,
  chunkIndex,
  isWorkflowRunning,
  onChunkReevaluation,
}: ChunkSidebarContentProps) {
  const chunkErrors = results.errors?.filter((error) => error.chunkIndex === chunkIndex) || [];
  const references = results.references || [];
  const chunk = results.chunks?.find((chunk) => chunk.chunkIndex === chunkIndex);
  const claims = chunk?.claims?.claims || [];
  const claimCommonKnowledgeResults = chunk?.claimCommonKnowledgeResults || [];
  const substantiations = chunk?.substantiations || [];
  const supportingFiles = results.supportingFiles || [];
  const shouldShowStatusBadge = useShouldShowStatusBadge(isWorkflowRunning);
  const citationSuggestions = chunk?.citationSuggestions || [];
  const liveReportsAnalysis = chunk?.liveReportsAnalysis || [];

  if (!chunk) {
    return null;
  }

  return (
    <div className="space-y-2">
      {shouldShowStatusBadge && <ChunkStatusBadge chunk={chunk} isWorkflowRunning={isWorkflowRunning} />}

      {chunkErrors.length > 0 && <ErrorsCard errors={chunkErrors} />}

      <div className="space-y-2">
        {claims.map((claim, index) => (
          <ClaimAnalysisCard
            key={index}
            claim={claim}
            commonKnowledgeResult={claimCommonKnowledgeResults.find((c) => c.claimIndex === index)}
            substantiation={substantiations.find((s) => s.claimIndex === index)}
            citationSuggestion={citationSuggestions.find((c) => c.claimIndex === index)}
            liveReportsAnalysis={liveReportsAnalysis.find((l) => l.claimIndex === index)}
            claimIndex={index}
            totalClaims={claims.length}
            references={references}
            supportingFiles={results.supportingFiles || []}
          />
        ))}
      </div>

      <ChunkAnalysisCard chunk={chunk} references={references} supportingFiles={supportingFiles} />

      <ChunkReevaluateControl
        chunkIndex={chunk.chunkIndex}
        originalState={results}
        onReevaluation={onChunkReevaluation}
        sessionId={results.config.sessionId}
      />

      <ChunkEvalGenerator chunkIndex={chunk.chunkIndex} originalState={results} />
    </div>
  );
}
