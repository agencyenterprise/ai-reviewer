'use client';

import { AiGeneratedLabel } from '@/components/ai-generated-label';
import { Markdown } from '@/components/markdown';
import { Badge } from '@/components/ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { claimCategoryBaseColors, classifyChunk } from '@/lib/claim-classification';
import {
  ChunkReevaluationResponse,
  CitationSuggestionResultWithClaimIndexOutput,
  ClaimSubstantiatorStateOutput,
  DocumentChunkOutput,
  Reference,
} from '@/lib/generated-api';
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

// Helper functions for sorting citation suggestions
const confidenceRank: Record<string, number> = {
  high: 3,
  medium: 2,
  low: 1,
};

const qualityRank: Record<string, number> = {
  high_impact_publication: 4,
  medium_impact_publication: 3,
  low_impact_publication: 2,
  not_a_publication: 1,
};

function scoreReference(ref: Reference) {
  const c =
    confidenceRank[(ref?.confidenceInRecommendation || '').toLowerCase?.() || ref?.confidenceInRecommendation] || 0;
  const q = qualityRank[(ref?.publicationQuality || '').toLowerCase?.() || ref?.publicationQuality] || 0;
  return c * 10 + q; // weight confidence higher than quality
}

function scoreSuggestion(s: CitationSuggestionResultWithClaimIndexOutput) {
  const refs = s?.relevantReferences || [];
  if (refs.length === 0) return 0;
  return Math.max(...refs.map(scoreReference));
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

  const sortedCitationSuggestions = React.useMemo(() => {
    const suggestions = chunk.citationSuggestions || [];
    return [...suggestions].sort((a, b) => scoreSuggestion(b) - scoreSuggestion(a));
  }, [chunk.citationSuggestions]);

  function toTitleCase(s: string) {
    return s?.replace(/_/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase()) || '';
  }

  function confidenceBadgeClasses(conf: string) {
    const k = (conf || '').toLowerCase();
    if (k === 'high') return 'bg-green-100 text-green-800';
    if (k === 'medium') return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  }

  function qualityBadgeClasses(qual: string) {
    const k = (qual || '').toLowerCase();
    if (k === 'high_impact_publication') return 'bg-emerald-100 text-emerald-800';
    if (k === 'medium_impact_publication') return 'bg-teal-100 text-teal-800';
    if (k === 'low_impact_publication') return 'bg-slate-100 text-slate-700';
    return 'bg-neutral-100 text-neutral-800';
  }

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

          {sortedCitationSuggestions.length > 0 && (
            <React.Fragment>
              <HorizontalSeparator />
              <p className="inline-flex items-center gap-1 text-purple-600 text-xs">
                <LinkIcon className="w-3 h-3" />
                {sortedCitationSuggestions.length} suggested citation{sortedCitationSuggestions.length > 1 ? 's' : ''}
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
            <Accordion type="single" collapsible className="border rounded-lg">
              <AccordionItem value="citations" className="border-none">
                <AccordionTrigger className="px-4 py-2 hover:no-underline">
                  <div className="flex items-center gap-2">
                    <LinkIcon className="w-4 h-4" />
                    <span className="font-bold">Citations ({citations.length})</span>
                    <span className="text-xs text-muted-foreground font-normal">
                      {citations.filter((c) => c.associatedBibliography).length} with bibliography
                    </span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-4 pb-4">
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
                              references[citation.indexOfAssociatedBibliography - 1]
                                ?.hasAssociatedSupportingDocument && (
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
                              !references[citation.indexOfAssociatedBibliography - 1]
                                .hasAssociatedSupportingDocument && (
                                <div className="text-xs text-muted-foreground mt-1">
                                  <strong>No related supporting document:</strong>
                                </div>
                              )}
                          </div>
                        )}
                      </ChunkItem>
                    ))}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          )}

          {sortedCitationSuggestions && sortedCitationSuggestions.length > 0 && (
            <Accordion type="single" collapsible className="border rounded-lg">
              <AccordionItem value="suggestions" className="border-none">
                <AccordionTrigger className="px-4 py-2 hover:no-underline">
                  <div className="flex items-center gap-2">
                    <LinkIcon className="w-4 h-4 text-purple-600" />
                    <span className="font-bold">Citation Suggestions ({sortedCitationSuggestions.length})</span>
                    <span className="text-xs text-muted-foreground font-normal">
                      {sortedCitationSuggestions.reduce((sum, s) => sum + (s.relevantReferences?.length || 0), 0)} total
                      references
                    </span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-4 pb-4">
                  <div className="space-y-4">
                    {sortedCitationSuggestions.map((suggestion, si) => {
                      const sortedRefs = [...(suggestion.relevantReferences || [])].sort(
                        (a, b) => scoreReference(b) - scoreReference(a),
                      );
                      return (
                        <div key={si} className="space-y-3">
                          <div className="text-sm text-muted-foreground">
                            <strong>
                              Claim {suggestion.claimIndex !== undefined ? suggestion.claimIndex + 1 : 'Unknown'}:
                            </strong>{' '}
                            {suggestion.rationale}
                          </div>
                          <div className="space-y-3">
                            {sortedRefs.map((reference, ri) => (
                              <ChunkItem key={ri}>
                                <div className="space-y-2">
                                  <div className="flex items-start justify-between">
                                    <h5 className="font-medium text-sm">{reference.title}</h5>
                                    <div className="flex items-center gap-2 flex-wrap">
                                      <span
                                        className={`px-2 py-1 rounded text-xs ${
                                          reference.type === 'article'
                                            ? 'bg-blue-100 text-blue-800'
                                            : reference.type === 'book'
                                              ? 'bg-green-100 text-green-800'
                                              : reference.type === 'webpage'
                                                ? 'bg-purple-100 text-purple-800'
                                                : 'bg-gray-100 text-gray-800'
                                        }`}
                                      >
                                        {reference.type}
                                      </span>
                                      {reference.isAlreadyCitedElsewhere && (
                                        <span className="px-2 py-1 rounded text-xs bg-cyan-100 text-cyan-800">
                                          Already cited
                                        </span>
                                      )}
                                      <span
                                        className={`px-2 py-1 rounded text-xs ${
                                          reference.recommendedAction === 'add_citation'
                                            ? 'bg-green-100 text-green-800'
                                            : reference.recommendedAction === 'replace_existing_reference'
                                              ? 'bg-yellow-100 text-yellow-800'
                                              : reference.recommendedAction === 'discuss_reference'
                                                ? 'bg-blue-100 text-blue-800'
                                                : reference.recommendedAction === 'no_action'
                                                  ? 'bg-gray-100 text-gray-800'
                                                  : 'bg-orange-100 text-orange-800'
                                        }`}
                                      >
                                        {reference.recommendedAction.replace('_', ' ')}
                                      </span>
                                      <span
                                        className={`px-2 py-1 rounded text-xs ${confidenceBadgeClasses(reference.confidenceInRecommendation)}`}
                                      >
                                        {toTitleCase(reference.confidenceInRecommendation)} Confidence
                                      </span>
                                      <span
                                        className={`px-2 py-1 rounded text-xs ${qualityBadgeClasses(reference.publicationQuality)}`}
                                      >
                                        {toTitleCase(reference.publicationQuality)}
                                      </span>
                                    </div>
                                  </div>

                                  <div className="text-xs text-muted-foreground">
                                    <p>
                                      <strong>Link:</strong>{' '}
                                      <a
                                        href={reference.link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:underline"
                                      >
                                        {reference.link}
                                      </a>
                                    </p>
                                  </div>

                                  <div className="text-xs">
                                    <p>
                                      <strong>Bibliography Entry:</strong>
                                    </p>
                                    <p className="text-muted-foreground italic">{reference.bibliographyInfo}</p>
                                  </div>

                                  <div className="text-xs">
                                    <p>
                                      <strong>Related Excerpt (from our document):</strong>
                                    </p>
                                    <p className="text-muted-foreground">&quot;{reference.relatedExcerpt}&quot;</p>
                                  </div>

                                  <div className="text-xs">
                                    <p>
                                      <strong>Related Excerpt (from reference):</strong>
                                    </p>
                                    <p className="text-muted-foreground">
                                      &quot;{reference.relatedExcerptFromReference}&quot;
                                    </p>
                                  </div>

                                  <div className="text-xs">
                                    <p>
                                      <strong>Rationale:</strong>
                                    </p>
                                    <p className="text-muted-foreground">{reference.rationale}</p>
                                  </div>

                                  <div className="text-xs">
                                    <p>
                                      <strong>Recommended Action:</strong>
                                    </p>
                                    <p className="text-muted-foreground">{reference.explanationForRecommendedAction}</p>
                                  </div>
                                </div>
                              </ChunkItem>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
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
