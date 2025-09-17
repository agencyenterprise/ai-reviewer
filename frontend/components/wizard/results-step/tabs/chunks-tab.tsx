'use client';

import * as React from 'react';
import { ChunkItem } from '../components/chunk-display';
import { AlertTriangle, FileIcon, Link as LinkIcon } from 'lucide-react';
import { ClaimSubstantiatorState } from '@/lib/generated-api';
import { getSeverityClasses, getSeverityLabel } from '@/lib/severity';

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
                      const severity = subst?.severity;
                      return (
                        <ChunkItem key={ci} className={isUnsubstantiated ? 'bg-red-50/40' : ''}>
                          <p className="text-sm">
                            <strong>Claim:</strong> {claim.claim}
                          </p>
                          <p className="text-sm text-muted-foreground mt-1">
                            <strong>Related Text:</strong> &quot;{claim.text}&quot;
                          </p>
                          {claim.rationale && (
                            <p className="text-xs text-muted-foreground mt-1">
                              <strong>Rationale:</strong> {claim.rationale}
                            </p>
                          )}
                          <div className="flex items-center gap-2 mt-1">
                            <span
                              className={`inline-flex items-center px-2 py-1 rounded text-xs ${
                                claim.needsSubstantiation
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}
                              title={
                                claim.needsSubstantiation
                                  ? 'This claim likely requires citation/backing in academic writing'
                                  : 'This claim may be considered common knowledge'
                              }
                            >
                              {claim.needsSubstantiation ? 'Needs Substantiation' : "Doesn't Need Substantiation"}
                            </span>
                            {typeof severity === 'number' && severity > 0 && (
                              <span
                                className={`inline-flex items-center px-2 py-1 rounded text-xs ${getSeverityClasses(
                                  severity,
                                )}`}
                                title={`Severity ${severity}: ${getSeverityLabel(severity)}`}
                              >
                                Severity: {getSeverityLabel(severity)}
                              </span>
                            )}
                            {claim.warrantExpression && (
                              <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 text-blue-800">
                                Warrant: {claim.warrantExpression}
                              </span>
                            )}
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-2">
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
