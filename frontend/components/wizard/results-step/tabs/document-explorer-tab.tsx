'use client';

import { ChunkReevaluationResponse, ClaimSubstantiatorStateOutput } from '@/lib/generated-api';
import { Loader2 } from 'lucide-react';
import * as React from 'react';
import { ErrorsCard } from '../components/errors-card';
import { useSupportedAgents } from '../hooks/use-supported-agents';
import { DocumentExplorerChunk } from './document-explorer-chunk';

interface DocumentExplorerTabProps {
  results: ClaimSubstantiatorStateOutput;
  onChunkReevaluation: (response: ChunkReevaluationResponse) => void;
  isProcessing?: boolean;
}

export function DocumentExplorerTab({ results, onChunkReevaluation, isProcessing = false }: DocumentExplorerTabProps) {
  const { supportedAgents, supportedAgentsError } = useSupportedAgents();

  const errors = results.errors || [];
  const workflowErrors = errors.filter((error) => error.chunkIndex === null);
  const hasChunks = (results.chunks?.length || 0) > 0;

  if (isProcessing && !hasChunks) {
    return (
      <div className="space-y-4">
        {workflowErrors.length > 0 && <ErrorsCard errors={workflowErrors} />}
        <div className="flex items-center justify-center py-12">
          <div className="text-center space-y-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
            <p className="text-sm text-muted-foreground">Breaking document into sections...</p>
          </div>
        </div>
      </div>
    );
  }

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
          isWorkflowRunning={isProcessing}
        />
      ))}
    </div>
  );
}
