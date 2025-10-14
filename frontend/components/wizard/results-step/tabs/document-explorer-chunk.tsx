'use client';

import { Markdown } from '@/components/markdown';
import { Badge } from '@/components/ui/badge';
import {
  ChunkReevaluationResponse,
  ClaimSubstantiatorStateOutput,
  DocumentChunkOutput,
  EvidenceAlignmentLevel,
} from '@/lib/generated-api';
import { scoreSuggestion } from '@/lib/reference-scoring';
import { getSeverity, severityColors } from '@/lib/severity';
import { AlertTriangleIcon, CheckCircleIcon, ChevronRight, Link as LinkIcon, MessageCirclePlus } from 'lucide-react';
import * as React from 'react';
import { ChunkEvalGenerator } from '../components/chunk-eval-generator';
import { ChunkReevaluateControl } from '../components/chunk-reevaluate-control';
import { ChunkStatusBadge } from '../components/chunk-status-badge';
import { ClaimAnalysisCard } from '../components/claim-analysis-card';
import { ErrorsCard } from '../components/errors-card';
import { EvidenceAlignmentLevelBadge } from '../components/evidence-alignment-level-badge';
import { useSupportedAgents } from '../hooks/use-supported-agents';
import { ChunkCitations } from './chunk-citations';
import { ChunkCitationSuggestions } from './chunk-citation-suggestions';

export interface DocumentExplorerChunkProps {
  chunk: DocumentChunkOutput;
  results: ClaimSubstantiatorStateOutput;
  onChunkReevaluation: (response: ChunkReevaluationResponse) => void;
  supportedAgents: ReturnType<typeof useSupportedAgents>['supportedAgents'];
  supportedAgentsError: ReturnType<typeof useSupportedAgents>['supportedAgentsError'];
  sessionId?: string | null;
  isWorkflowRunning: boolean;
}

export function DocumentExplorerChunk({
  chunk,
  results,
  onChunkReevaluation,
  supportedAgents,
  supportedAgentsError,
  sessionId,
  isWorkflowRunning,
}: DocumentExplorerChunkProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  const claims = chunk.claims?.claims || [];
  const claimsLength = claims.length || 0;
  const noClaims = claimsLength === 0;
  const claimsRationale = chunk.claims?.rationale;
  const citations = chunk.citations?.citations || [];
  const references = results.references || [];
  const supportingFiles = results.supportingFiles || [];
  const claimCommonKnowledgeResults = chunk.claimCommonKnowledgeResults || [];
  const substantiations = chunk.substantiations || [];
  const errors = results.errors || [];
  const chunkErrors = errors.filter((error) => error.chunkIndex === chunk.chunkIndex);
  const evidenceAlignmentCounts = chunk.substantiations?.reduce(
    (acc, substantiation) => {
      acc[substantiation.evidenceAlignment] = (acc[substantiation.evidenceAlignment] || 0) + 1;
      return acc;
    },
    {} as Record<EvidenceAlignmentLevel, number>,
  );
  const commonKnowledgeCounts =
    chunk.claimCommonKnowledgeResults?.reduce(
      (acc, commonKnowledgeResult) => (commonKnowledgeResult.isCommonKnowledge ? acc + 1 : acc),
      0,
    ) ?? 0;
  const severity = getSeverity(chunk);

  const sortedCitationSuggestions = React.useMemo(() => {
    const suggestions = chunk.citationSuggestions || [];
    return [...suggestions].sort((a, b) => scoreSuggestion(b) - scoreSuggestion(a));
  }, [chunk.citationSuggestions]);

  return (
    <div>
      <Markdown highlight={severityColors[severity]}>{chunk.content}</Markdown>

      <div
        className="flex items-center space-x-1 cursor-pointer hover:bg-muted/50 rounded-lg px-2"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <ChevronRight className={`w-3 h-3 ${isExpanded ? 'rotate-90' : ''}`} />

        <div className="flex flex-wrap items-center">
          <p className="text-xs text-muted-foreground">Chunk {chunk.chunkIndex + 1}</p>

          <HorizontalSeparator />
          <ChunkStatusBadge chunk={chunk} isWorkflowRunning={isWorkflowRunning} />
          <HorizontalSeparator />

          {noClaims && <p className="text-xs text-muted-foreground">No claims</p>}

          {claimsLength > 0 && (
            <p className="text-xs text-muted-foreground inline-flex items-center gap-1">
              <MessageCirclePlus className="w-3 h-3" />
              {claimsLength} claim{claimsLength > 1 ? 's' : ''}
            </p>
          )}

          {citations.length > 0 && (
            <React.Fragment>
              <HorizontalSeparator />
              <p className="inline-flex items-center gap-1 text-blue-600 text-xs">
                <LinkIcon className="w-3 h-3" />
                {citations.length} citation{citations.length > 1 ? 's' : ''}
              </p>
            </React.Fragment>
          )}

          {sortedCitationSuggestions.length > 0 && (
            <React.Fragment>
              <HorizontalSeparator />
              <p className="inline-flex items-center gap-1 text-purple-600 text-xs">
                <LinkIcon className="w-3 h-3" />
                {sortedCitationSuggestions.length} suggested citation{sortedCitationSuggestions.length > 1 ? 's' : ''}
              </p>
            </React.Fragment>
          )}

          {commonKnowledgeCounts > 0 && (
            <React.Fragment>
              <HorizontalSeparator />
              <Badge variant="success" className="font-normal bg-transparent p-0 m-0 text-green-600">
                <CheckCircleIcon className="w-3 h-3" />
                {commonKnowledgeCounts} Common knowledge claim{commonKnowledgeCounts > 1 ? 's' : ''}
              </Badge>
            </React.Fragment>
          )}

          {Object.entries(evidenceAlignmentCounts || {}).map(([evidenceAlignment, count]) => (
            <React.Fragment key={evidenceAlignment}>
              <HorizontalSeparator />

              <EvidenceAlignmentLevelBadge
                evidenceAlignment={evidenceAlignment as EvidenceAlignmentLevel}
                variant="text"
                count={count}
                className="font-normal"
              />
            </React.Fragment>
          ))}

          {chunkErrors.length > 0 && (
            <React.Fragment>
              <HorizontalSeparator />
              <Badge variant="destructive" className="font-medium">
                <AlertTriangleIcon />
                {chunkErrors.length} processing error{chunkErrors.length > 1 ? 's' : ''}
              </Badge>
            </React.Fragment>
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-4 bg-muted/50 p-4 rounded-lg mt-2 ml-8 text-sm">
          {chunkErrors.length > 0 && <ErrorsCard errors={chunkErrors} />}

          <div className="space-y-2">
            {claims.map((claim, index) => {
              return (
                <ClaimAnalysisCard
                  key={index}
                  claim={claim}
                  commonKnowledgeResult={claimCommonKnowledgeResults.find((c) => c.claimIndex === index)}
                  substantiation={substantiations.find((s) => s.claimIndex === index)}
                  claimIndex={index}
                  totalClaims={claims.length}
                />
              );
            })}
          </div>

          <ChunkCitations citations={citations} references={references} supportingFiles={supportingFiles} />

          <ChunkCitationSuggestions suggestions={sortedCitationSuggestions} references={references} />

          <p className="mb-2">
            <span className="font-bold mb-2 flex items-center gap-2">Claim extraction rationale:</span>
            {claimsRationale}
          </p>

          <ChunkReevaluateControl
            chunkIndex={chunk.chunkIndex}
            originalState={results}
            onReevaluation={onChunkReevaluation}
            supportedAgents={supportedAgents}
            supportedAgentsError={supportedAgentsError}
            sessionId={sessionId}
          />

          <ChunkEvalGenerator
            chunkIndex={chunk.chunkIndex}
            originalState={results}
            supportedAgents={supportedAgents}
            supportedAgentsError={supportedAgentsError}
          />
        </div>
      )}
    </div>
  );
}

export function HorizontalSeparator() {
  return <span className="text-lg mx-2">·</span>;
}
