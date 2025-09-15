'use client';

import { ClaimSubstantiatorState } from '@/lib/generated-api';
import * as React from 'react';

interface SummaryTabProps {
  results: ClaimSubstantiatorState;
  totalChunks: number;
  chunksWithClaims: number;
  chunksWithCitations: number;
  supportedReferences: number;
}

export function SummaryTab({
  results,
  totalChunks,
  chunksWithClaims,
  chunksWithCitations,
  supportedReferences,
}: SummaryTabProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Analysis Summary</h3>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-muted-foreground">Total chunks:</span>
          <span className="ml-2 font-medium">{totalChunks}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Chunks with claims:</span>
          <span className="ml-2 font-medium">{chunksWithClaims}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Chunks with citations:</span>
          <span className="ml-2 font-medium">{chunksWithCitations}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Total references:</span>
          <span className="ml-2 font-medium">{results.references?.length}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Supported references:</span>
          <span className="ml-2 font-medium">{supportedReferences}</span>
        </div>
      </div>
    </div>
  );
}
