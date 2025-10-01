'use client';

import * as React from 'react';
import { ChunkDisplay, ChunkItem } from '../components/chunk-display';
import { CommonKnowledgeBadge } from '../components/common-knowledge-badge';
import { ClaimSubstantiatorStateOutput } from '@/lib/generated-api';
import { classifyClaim } from '@/lib/claim-classification';
import { FeedbackSection } from '../components/feedback-section';

interface ClaimsTabProps {
  results: ClaimSubstantiatorStateOutput;
}

export function ClaimsTab({ results }: ClaimsTabProps) {
  const claimsWithSubstantiation = results.chunks?.map((chunk) => ({
    ...chunk,
    claimCommonKnowledgeResults: chunk.claimCommonKnowledgeResults || [],
    substantiations: chunk.substantiations || [],
  }));

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Claims Analysis</h3>
      <div className="space-y-4">
        {claimsWithSubstantiation?.map(
          (chunk, chunkIndex) =>
            (chunk.claims?.claims?.length || 0) > 0 && (
              <ChunkDisplay key={chunkIndex} chunkIndex={chunkIndex}>
                {chunk.claims?.claims?.map((claim, claimIndex) => {
                  const commonKnowledgeResult = chunk.claimCommonKnowledgeResults[claimIndex];
                  return (
                    <ChunkItem key={claimIndex}>
                      <p className="text-sm mb-2">
                        <strong>Claim:</strong> {claim.claim}
                      </p>
                      <p className="text-xs text-muted-foreground mb-2">
                        <strong>Text:</strong> &quot;{claim.text}&quot;
                      </p>
                      {claim.rationale && (
                        <p className="text-xs text-muted-foreground mb-2">
                          <strong>Rationale:</strong> {claim.rationale}
                        </p>
                      )}
                      <div className="flex items-center gap-2 mb-2">
                        <div
                          className={`inline-flex items-center px-2 py-1 rounded text-xs ${
                            commonKnowledgeResult?.needsSubstantiation
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                          title={
                            commonKnowledgeResult?.needsSubstantiation
                              ? 'This claim likely requires citation/backing in academic writing'
                              : 'This claim may be considered common knowledge'
                          }
                        >
                          {commonKnowledgeResult?.needsSubstantiation
                            ? 'Needs Substantiation'
                            : "Doesn't Need Substantiation"}
                        </div>
                        {claim.warrantExpression && (
                          <div className="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 text-blue-800">
                            Warrant: {claim.warrantExpression}
                          </div>
                        )}
                      </div>

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
                      {chunk.substantiations[claimIndex] && (
                        <div className="mt-2">
                          <div className="flex items-center gap-2 flex-wrap mb-2">
                            <div
                              className={`inline-flex items-center px-2 py-1 rounded text-xs ${
                                chunk.substantiations[claimIndex].isSubstantiated
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-red-100 text-red-800'
                              }`}
                            >
                              {chunk.substantiations[claimIndex].isSubstantiated ? 'Substantiated' : 'Unsubstantiated'}
                            </div>
                            <CommonKnowledgeBadge
                              isCommonKnowledge={commonKnowledgeResult?.isCommonKnowledge || false}
                              commonKnowledgeRationale={commonKnowledgeResult?.rationale}
                              claimCategory={classifyClaim(
                                commonKnowledgeResult,
                                chunk.substantiations[claimIndex],
                                chunk.citations?.citations || [],
                                results.references || [],
                              )}
                            />
                          </div>
                          {chunk.substantiations[claimIndex].feedback && (
                            <FeedbackSection
                              claim={claim}
                              commonKnowledgeResult={commonKnowledgeResult}
                              substantiation={chunk.substantiations[claimIndex]}
                              citations={chunk.citations?.citations || []}
                              references={results.references || []}
                              feedback={chunk.substantiations[claimIndex].feedback}
                            />
                          )}
                        </div>
                      )}
                    </ChunkItem>
                  );
                })}
              </ChunkDisplay>
            ),
        )}
      </div>
    </div>
  );
}
