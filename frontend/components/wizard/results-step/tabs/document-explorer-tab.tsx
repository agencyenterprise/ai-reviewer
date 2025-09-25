'use client';

import { AiGeneratedLabel } from '@/components/ai-generated-label';
import { Markdown } from '@/components/markdown';
import { Badge } from '@/components/ui/badge';
import { claimCategoryBaseColors, classifyChunk, classifyClaim } from '@/lib/claim-classification';
import { ChunkReevaluationResponse, ClaimSubstantiatorStateOutput, DocumentChunkOutput } from '@/lib/generated-api';
import { getMaxSeverity } from '@/lib/severity';
import { cn } from '@/lib/utils';
import { AlertTriangleIcon, ChevronRight, FileIcon, Link as LinkIcon, MessageCirclePlus } from 'lucide-react';
import * as React from 'react';
import { useWizard } from '../../wizard-context';
import { ChunkItem } from '../components/chunk-display';
import { ChunkEvalGenerator } from '../components/chunk-eval-generator';
import { ChunkReevaluateControl } from '../components/chunk-reevaluate-control';
import { ClaimCategoryLabel } from '../components/claim-category-label';
import { ErrorsCard } from '../components/errors-card';
import { SeverityBadge } from '../components/severity-badge';
import { CommonKnowledgeBadge } from '../components/common-knowledge-badge';
import { useSupportedAgents } from '../hooks/use-supported-agents';

interface DocumentExplorerTabProps {
  results: ClaimSubstantiatorStateOutput;
}

export function DocumentExplorerTab({ results }: DocumentExplorerTabProps) {
  const { state, actions } = useWizard();
  const { supportedAgents, supportedAgentsError } = useSupportedAgents();

  const errors = results.errors || [];
  const workflowErrors = errors.filter((error) => error.chunkIndex === null);

  const handleChunkReevaluation = (response: ChunkReevaluationResponse) => {
    actions.updateChunkResults(response);
  };

  return (
    <div className="space-y-2">
      {workflowErrors.length > 0 && <ErrorsCard errors={workflowErrors} />}

      {results.chunks?.map((chunk) => (
        <DocumentExplorerChunk
          key={chunk.chunkIndex}
          chunk={chunk}
          results={results}
          onChunkReevaluation={handleChunkReevaluation}
          supportedAgents={supportedAgents}
          supportedAgentsError={supportedAgentsError}
          sessionId={state.sessionId}
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
              const subst = substantiations[ci];
              const isUnsubstantiated = subst ? !subst.isSubstantiated : false;
              const claimCategory = classifyClaim(claim, subst, citations, references);
              const severity = subst?.severity;

              return (
                <ChunkItem key={ci} className={cn(isUnsubstantiated ? 'bg-red-50/40' : '', 'space-y-2')}>
                  <p className="flex items-center gap-1">
                    <ClaimCategoryLabel category={claimCategory} />
                    <SeverityBadge severity={severity} />
                    <CommonKnowledgeBadge isCommonKnowledge={subst?.isCommonKnowledge || false} />
                  </p>
                  <p>
                    <strong>Claim:</strong> {claim.claim}
                  </p>
                  <p>
                    <strong>Related Text:</strong> &quot;{claim.text}&quot;
                  </p>
                  <p>
                    <strong>Needs substantiation:</strong> {claim.needsSubstantiation ? 'Yes' : 'No'} -{' '}
                    {claim.rationale}
                  </p>
                  {claim.warrantExpression && (
                    <div className="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 text-blue-800">
                      Warrant: {claim.warrantExpression}
                    </div>
                  )}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <p className="text-xs font-semibold mb-1">Data / Grounds</p>
                      {claim.data && claim.data.length > 0 ? (
                        <ul className="list-disc pl-5 text-xs text-muted-foreground space-y-1">
                          {claim.data.map((d, i) => (
                            <li key={i}>{d}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-muted-foreground">None</p>
                      )}
                    </div>
                    <div>
                      <p className="text-xs font-semibold mb-1">Warrants</p>
                      {claim.warrants && claim.warrants.length > 0 ? (
                        <ul className="list-disc pl-5 text-xs text-muted-foreground space-y-1">
                          {claim.warrants.map((w, i) => (
                            <li key={i}>{w}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-muted-foreground">None</p>
                      )}
                    </div>
                    <div>
                      <p className="text-xs font-semibold mb-1">Qualifiers</p>
                      {claim.qualifiers && claim.qualifiers.length > 0 ? (
                        <ul className="list-disc pl-5 text-xs text-muted-foreground space-y-1">
                          {claim.qualifiers.map((q, i) => (
                            <li key={i}>{q}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-muted-foreground">None</p>
                      )}
                    </div>
                    <div>
                      <p className="text-xs font-semibold mb-1">Rebuttals</p>
                      {claim.rebuttals && claim.rebuttals.length > 0 ? (
                        <ul className="list-disc pl-5 text-xs text-muted-foreground space-y-1">
                          {claim.rebuttals.map((r, i) => (
                            <li key={i}>{r}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-muted-foreground">None</p>
                      )}
                    </div>
                    <div className="md:col-span-2">
                      <p className="text-xs font-semibold mb-1">Backing</p>
                      {claim.backing && claim.backing.length > 0 ? (
                        <ul className="list-disc pl-5 text-xs text-muted-foreground space-y-1">
                          {claim.backing.map((b, i) => (
                            <li key={i}>{b}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-muted-foreground">None</p>
                      )}
                    </div>
                  </div>
                  {subst && subst.isSubstantiated && (
                    <p className="text-green-600">
                      <strong>Substantiated because:</strong> {subst.rationale}
                    </p>
                  )}
                  {subst && !subst.isSubstantiated && (
                    <>
                      <p className="text-red-600">
                        <strong>Unsubstantiated because:</strong> {subst.rationale}
                      </p>
                      {subst.feedback && (
                        <p className="text-blue-600">
                          <strong>Feedback to resolve:</strong> {subst.feedback}
                        </p>
                      )}
                    </>
                  )}
                </ChunkItem>
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
