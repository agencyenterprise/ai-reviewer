'use client';

import { ClaimSubstantiatorState } from '@/lib/generated-api';
import { AlertTriangle, ChevronRight, FileIcon, Link as LinkIcon, MessageCirclePlus } from 'lucide-react';
import * as React from 'react';
import { ChunkItem } from '../components/chunk-display';
import { Markdown } from '@/components/markdown';
import { AiGeneratedLabel } from '@/components/ai-generated-label';
import { cn } from '@/lib/utils';

interface DocumentExplorerTabProps {
  results: ClaimSubstantiatorState;
}

export function DocumentExplorerTab({ results }: DocumentExplorerTabProps) {
  return (
    <div className="space-y-2">
      {results.chunks?.map((_, chunkIndex) => (
        <DocumentExplorerChunk key={chunkIndex} results={results} chunkIndex={chunkIndex} />
      ))}
    </div>
  );
}

export interface DocumentExplorerChunkProps {
  results: ClaimSubstantiatorState;
  chunkIndex: number;
}

export function DocumentExplorerChunk({ results, chunkIndex }: DocumentExplorerChunkProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  const chunk = results.chunks?.[chunkIndex];
  const claims = results.claimsByChunk?.[chunkIndex]?.claims || [];
  const claimsLength = claims.length || 0;
  const noClaims = claimsLength === 0;
  const claimsRationale = results.claimsByChunk?.[chunkIndex]?.rationale;
  const citations = results.citationsByChunk?.[chunkIndex]?.citations || [];
  const references = results.references || [];
  const supportingFiles = results.supportingFiles || [];
  const substantiations = results.claimSubstantiationsByChunk?.[chunkIndex] || [];
  const unsubstantiatedClaims = substantiations.filter((s) => !s.isSubstantiated) || [];
  const hasUnsubstantiatedClaim = unsubstantiatedClaims.length > 0;

  return (
    <div key={chunkIndex}>
      <Markdown>{chunk}</Markdown>

      <div
        className="flex items-center space-x-1 cursor-pointer hover:bg-muted/50 rounded-lg px-2"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <ChevronRight className={`w-3 h-3 ${isExpanded ? 'rotate-90' : ''}`} />

        <div className="flex flex-wrap items-center">
          <p className="text-xs text-muted-foreground">Chunk {chunkIndex + 1}</p>

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

          {hasUnsubstantiatedClaim && (
            <React.Fragment>
              <HorizontalSeparator />
              <p className="inline-flex items-center gap-1 text-red-600 text-xs">
                <AlertTriangle className="w-3 h-3" />
                {unsubstantiatedClaims.length} unsubstantiated claim{unsubstantiatedClaims.length > 1 ? 's' : ''}
              </p>
            </React.Fragment>
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-4 bg-muted/50 p-4 rounded-lg mt-2 ml-8 text-sm">
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
              return (
                <ChunkItem key={ci} className={cn(isUnsubstantiated ? 'bg-red-50/40' : '', 'space-y-2')}>
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
                  {subst && subst.isSubstantiated && (
                    <p className="text-green-600 mt-1">
                      <strong>Substantiated because:</strong> {subst.rationale}
                    </p>
                  )}
                  {subst && !subst.isSubstantiated && (
                    <>
                      <p className="text-red-600 mt-1">
                        <strong>Unsubstantiated because:</strong> {subst.rationale}
                      </p>
                      {subst.feedback && (
                        <p className="text-blue-600 mt-1">
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
        </div>
      )}
    </div>
  );
}

export function HorizontalSeparator() {
  return <span className="text-lg mx-2">·</span>;
}
