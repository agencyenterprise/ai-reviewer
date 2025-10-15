'use client';

import * as React from 'react';
import { ChunkDisplay, ChunkItem } from '../components/chunk-display';
import { ClaimSubstantiatorStateOutput } from '@/lib/generated-api';
import { BookOpen } from 'lucide-react';
import { TabWithLoadingStates } from './tab-with-loading-states';

interface CitationsTabProps {
  results: ClaimSubstantiatorStateOutput;
  isProcessing?: boolean;
}

export function CitationsTab({ results, isProcessing = false }: CitationsTabProps) {
  return (
    <TabWithLoadingStates
      title="Citations Analysis"
      data={results.chunks}
      isProcessing={isProcessing}
      hasData={(chunks) => chunks?.some((c) => (c.citations?.citations?.length || 0) > 0) || false}
      loadingMessage={{
        title: 'Detecting citations...',
        description: 'Analyzing document for citation patterns',
      }}
      emptyMessage={{
        icon: <BookOpen className="h-12 w-12 text-muted-foreground" />,
        title: 'No citations found',
        description: "This document doesn't contain formal citations or references",
      }}
      skeletonType="list"
      skeletonCount={3}
    >
      {(chunks) => {
        const chunksWithCitations = chunks.filter((chunk) => (chunk.citations?.citations?.length || 0) > 0);
        return (
          <div className="space-y-4">
            {chunksWithCitations.map((chunk) => (
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
            ))}
          </div>
        );
      }}
    </TabWithLoadingStates>
  );
}
