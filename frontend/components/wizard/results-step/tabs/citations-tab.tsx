'use client';

import * as React from 'react';
import { ChunkDisplay, ChunkItem } from '../components/chunk-display';
import { ClaimSubstantiatorStateOutput } from '@/lib/generated-api';

interface CitationsTabProps {
  results: ClaimSubstantiatorStateOutput;
}

export function CitationsTab({ results }: CitationsTabProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Citations Analysis</h3>
      <div className="space-y-4">
        {results.chunks?.map(
          (chunk) =>
            (chunk.citations?.citations?.length || 0) > 0 && (
              <ChunkDisplay key={chunk.chunkIndex} chunkIndex={chunk.chunkIndex}>
                {chunk.citations?.citations?.map((citation, citationIndex) => (
                  <ChunkItem key={citationIndex}>
                    <p className="text-sm mb-2">
                      <strong>Citation:</strong> {citation.text}
                    </p>
                    <div className="flex gap-2 text-xs">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">{citation.type}</span>
                      <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded">{citation.format}</span>
                    </div>
                    {citation.associatedBibliography && (
                      <p className="text-xs text-muted-foreground mt-2">
                        <strong>Bibliography:</strong> {citation.associatedBibliography}
                      </p>
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
