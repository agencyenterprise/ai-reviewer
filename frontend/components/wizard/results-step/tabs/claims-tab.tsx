'use client';

import * as React from 'react';
import { ChunkDisplay, ChunkItem } from '../components/chunk-display';
import { ClaimSubstantiatorState } from '@/lib/generated-api';

interface ClaimsTabProps {
  results: ClaimSubstantiatorState;
}

export function ClaimsTab({ results }: ClaimsTabProps) {
  const claimsWithSubstantiation = results.claimsByChunk?.map((chunk, chunkIndex) => ({
    ...chunk,
    substantiations: results.claimSubstantiationsByChunk?.[chunkIndex] || [],
  }));

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Claims Analysis</h3>
      <div className="space-y-4">
        {claimsWithSubstantiation?.map(
          (chunk, chunkIndex) =>
            chunk.claims.length > 0 && (
              <ChunkDisplay key={chunkIndex} chunkIndex={chunkIndex}>
                {chunk.claims.map((claim, claimIndex) => (
                  <ChunkItem key={claimIndex}>
                    <p className="text-sm mb-2">
                      <strong>Claim:</strong> {claim.claim}
                    </p>
                    <p className="text-xs text-muted-foreground mb-2">
                      <strong>Text:</strong> &quot;{claim.text}&quot;
                    </p>
                    {chunk.substantiations[claimIndex] && (
                      <div className="mt-2">
                        <div
                          className={`inline-flex items-center px-2 py-1 rounded text-xs ${
                            chunk.substantiations[claimIndex].isSubstantiated
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {chunk.substantiations[claimIndex].isSubstantiated ? 'Substantiated' : 'Unsubstantiated'}
                        </div>
                        {chunk.substantiations[claimIndex].feedback && (
                          <p className="text-xs text-muted-foreground mt-1">
                            <strong>Feedback:</strong> {chunk.substantiations[claimIndex].feedback}
                          </p>
                        )}
                      </div>
                    )}
                  </ChunkItem>
                ))}
              </ChunkDisplay>
            ),
        )}
      </div>
    </div>
  );
}
