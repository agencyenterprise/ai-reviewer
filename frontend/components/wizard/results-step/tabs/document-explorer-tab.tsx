'use client';

import { AiGeneratedLabel } from '@/components/ai-generated-label';
import { Markdown } from '@/components/markdown';
import { Badge } from '@/components/ui/badge';
import { claimCategoryBaseColors, classifyChunk } from '@/lib/claim-classification';
import { ChunkReevaluationResponse, ClaimSubstantiatorStateOutput, DocumentChunkOutput } from '@/lib/generated-api';
import { getMaxSeverity } from '@/lib/severity';
import { AlertTriangleIcon, ChevronRight, FileIcon, Link as LinkIcon, MessageCirclePlus } from 'lucide-react';
import * as React from 'react';
import { ChunkItem } from '../components/chunk-display';
import { ChunkEvalGenerator } from '../components/chunk-eval-generator';
import { ChunkReevaluateControl } from '../components/chunk-reevaluate-control';
import { ErrorsCard } from '../components/errors-card';
import { ClaimAnalysisCard } from '../components/claim-analysis-card';
import { ClaimCategoryLabel } from '../components/claim-category-label';
import { SeverityBadge } from '../components/severity-badge';
import { useSupportedAgents } from '../hooks/use-supported-agents';

interface DocumentExplorerTabProps {
  results: ClaimSubstantiatorStateOutput;
  onChunkReevaluation: (response: ChunkReevaluationResponse) => void;
}

export function DocumentExplorerTab({ results, onChunkReevaluation }: DocumentExplorerTabProps) {
  const { supportedAgents, supportedAgentsError } = useSupportedAgents();

  const errors = results.errors || [];
  const workflowErrors = errors.filter((error) => error.chunkIndex === null);

  return (
    <div className="space-y-2">
      {workflowErrors.length > 0 && <ErrorsCard errors={workflowErrors} />}

      {results.chunks?.map((chunk) => (
        <DocumentExplorerChunk
          key={chunk.chunkIndex}
          chunk={chunk}
          results={results}
          supportedAgents={supportedAgents}
          supportedAgentsError={supportedAgentsError}
          sessionId={results.config.sessionId}
          onChunkReevaluation={onChunkReevaluation}
        />
      ))}
    </div>
  );
}

export interface DocumentExplorerChunkProps {
  chunk: DocumentChunkOutput;
  results: ClaimSubstantiatorStateOutput;
  onChunkReevaluation: (response: ChunkReevaluationResponse) => void;
  supportedAgents: ReturnType<typeof useSupportedAgents>['supportedAgents'];
  supportedAgentsError: ReturnType<typeof useSupportedAgents>['supportedAgentsError'];
  sessionId?: string | null;
}

export function DocumentExplorerChunk({
  chunk,
  results,
  onChunkReevaluation,
  supportedAgents,
  supportedAgentsError,
  sessionId,
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
  const chunkCategory = classifyChunk(chunk, references);
  const maxSeverity = getMaxSeverity(substantiations);
  const errors = results.errors || [];
  const chunkErrors = errors.filter((error) => error.chunkIndex === chunk.chunkIndex);

  return (
    <div>
      <Markdown highlight={claimCategoryBaseColors[chunkCategory]}>{chunk.content}</Markdown>

      <div
        className="flex items-center space-x-1 cursor-pointer hover:bg-muted/50 rounded-lg px-2"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <ChevronRight className={`w-3 h-3 ${isExpanded ? 'rotate-90' : ''}`} />

        <div className="flex flex-wrap items-center">
          <p className="text-xs text-muted-foreground">Chunk {chunk.chunkIndex + 1}</p>

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

          <HorizontalSeparator />
          <ClaimCategoryLabel category={chunkCategory} badge={false} className="cursor-pointer" />

          {maxSeverity > 0 && (
            <React.Fragment>
              <HorizontalSeparator />
              <SeverityBadge severity={maxSeverity} />
            </React.Fragment>
          )}

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

          <AiGeneratedLabel className="float-right" />

          <h4 className="font-bold mb-2 flex items-center gap-2">
            <MessageCirclePlus className="w-4 h-4" />
            Claims
          </h4>
          <p className="mb-2">
            <span className="font-medium">Rationale:</span> {claimsRationale}
          </p>
          <div className="space-y-2">
            {claims.map((claim, ci) => {
              return (
                <ClaimAnalysisCard
                  key={ci}
                  claim={claim}
                  commonKnowledgeResult={claimCommonKnowledgeResults[ci]}
                  substantiation={substantiations[ci]}
                  citations={citations}
                  references={references}
                />
              );
            })}
          </div>

          {citations.length > 0 && (
            <div>
              <h4 className="font-bold mb-2 flex items-center gap-2">
                <LinkIcon className="w-4 h-4" />
                Citations
              </h4>
              <div className="space-y-2">
                {citations.map((citation, ci) => (
                  <ChunkItem key={ci}>
                    <p className="">
                      <strong>Citation:</strong> {citation.text}
                    </p>
                    <div className="flex gap-2 text-xs mt-1">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">{citation.type}</span>
                      <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded">{citation.format}</span>
                    </div>
                    {citation.associatedBibliography && (
                      <div className="text-xs text-muted-foreground mt-1">
                        <strong>Associated bibliography:</strong> {citation.associatedBibliography}
                        {citation.format &&
                          references[citation.indexOfAssociatedBibliography - 1]?.hasAssociatedSupportingDocument && (
                            <div className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                              <strong>Related supporting document:</strong>
                              <FileIcon className="w-3 h-3" />
                              {
                                supportingFiles[
                                  references[citation.indexOfAssociatedBibliography - 1]
                                    ?.indexOfAssociatedSupportingDocument - 1
                                ]?.fileName
                              }
                            </div>
                          )}
                        {citation.indexOfAssociatedBibliography &&
                          references[citation.indexOfAssociatedBibliography - 1] &&
                          !references[citation.indexOfAssociatedBibliography - 1].hasAssociatedSupportingDocument && (
                            <div className="text-xs text-muted-foreground mt-1">
                              <strong>No related supporting document:</strong>
                            </div>
                          )}
                      </div>
                    )}
                  </ChunkItem>
                ))}
              </div>
            </div>
          )}

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
