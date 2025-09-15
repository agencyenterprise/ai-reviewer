'use client';

import * as React from 'react';
import { ChunkItem } from '../components/chunk-display';
import { AlertTriangle, FileIcon, Link as LinkIcon } from 'lucide-react';
import { ClaimSubstantiatorState } from '@/lib/generated-api';

interface ChunksTabProps {
  results: ClaimSubstantiatorState;
}

export function ChunksTab({ results }: ChunksTabProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Chunks</h3>
      <div className="space-y-4">
        {results.claimsByChunk?.map((claimsChunk, chunkIndex) => {
          const chunk = results.chunks?.[chunkIndex];
          const claimsRationale = claimsChunk.rationale;
          const claims = claimsChunk?.claims || [];
          const substantiations = results.claimSubstantiationsByChunk?.[chunkIndex] || [];
          const references = results.references || [];
          const supportingFiles = results.supportingFiles || [];
          const citationsChunk = results.citationsByChunk?.[chunkIndex];
          const citations = citationsChunk?.citations || [];
          const chunkText = chunk || 'No content provided.';
          const hasUnsubstantiated = (results.claimSubstantiationsByChunk?.[chunkIndex] || []).some(
            (s) => !s.isSubstantiated,
          );

          return (
            <div
              key={chunkIndex}
              className={`border rounded-lg ${hasUnsubstantiated ? 'border-red-200 bg-red-50/40' : ''}`}
            >
              <div
                className={`flex items-center justify-between px-4 py-2 border-b ${hasUnsubstantiated ? 'bg-red-50' : 'bg-muted/50'}`}
              >
                <div className="flex items-center gap-2">
                  <span className="font-medium">Chunk {chunkIndex + 1}</span>
                  {hasUnsubstantiated && (
                    <span
                      title="Unsubstantiated claims present"
                      className="inline-flex items-center gap-1 text-red-600 text-xs"
                    >
                      <AlertTriangle className="w-3 h-3" />
                      Unsubstantiated
                    </span>
                  )}
                </div>
                {citations.length > 0 && (
                  <span className="inline-flex items-center gap-1 text-blue-600 text-xs">
                    <LinkIcon className="w-3 h-3" />
                    {citations.length} citation{citations.length > 1 ? 's' : ''}
                  </span>
                )}
              </div>

              <div className="p-4 space-y-4">
                <h4 className="text-sm font-medium mb-2">Text</h4>
                <ChunkItem>
                  <p className="text-sm whitespace-pre-wrap">{chunkText}</p>
                </ChunkItem>

                <div>
                  <h4 className="text-sm font-medium mb-2">Claims</h4>
                  <p className="text-sm text-muted-foreground mb-2">
                    <strong>Rationale:</strong> {claimsRationale}
                  </p>
                  <div className="space-y-2">
                    {claims.map((claim, ci) => {
                      const subst = substantiations[ci];
                      const isUnsubstantiated = subst ? !subst.isSubstantiated : false;
                      return (
                        <ChunkItem key={ci} className={isUnsubstantiated ? 'bg-red-50/40' : ''}>
                          <p className="text-sm">
                            <strong>Claim:</strong> {claim.claim}
                          </p>
                          <p className="text-sm text-muted-foreground mt-1">
                            <strong>Related Text:</strong> &quot;{claim.text}&quot;
                          </p>
                          {subst && subst.isSubstantiated && (
                            <p className="text-sm text-green-600 mt-1">
                              <strong>Substantiated because:</strong> {subst.rationale}
                            </p>
                          )}
                          {subst && !subst.isSubstantiated && (
                            <>
                              <p className="text-sm text-red-600 mt-1">
                                <strong>Unsubstantiated because:</strong> {subst.rationale}
                              </p>
                              {subst.feedback && (
                                <p className="text-sm text-blue-600 mt-1">
                                  <strong>Feedback to resolve:</strong> {subst.feedback}
                                </p>
                              )}
                            </>
                          )}
                        </ChunkItem>
                      );
                    })}
                  </div>
                </div>

                {citations.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-2">Citations</h4>
                    <div className="space-y-2">
                      {citations.map((citation, ci) => (
                        <ChunkItem key={ci}>
                          <p className="text-sm">
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
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
