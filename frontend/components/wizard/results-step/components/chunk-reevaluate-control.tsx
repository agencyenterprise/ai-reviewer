'use client';

import { analysisService } from '@/lib/analysis-service';
import {
  ChunkReevaluationRequest,
  ChunkReevaluationResponse,
  ClaimSubstantiatorStateOutput,
} from '@/lib/generated-api';
import * as React from 'react';
import { useSupportedAgents } from '../hooks/use-supported-agents';
import { ExpandableControl } from './expandable-control';

interface ChunkReevaluateControlProps {
  chunkIndex: number;
  originalState: ClaimSubstantiatorStateOutput;
  onReevaluation: (response: ChunkReevaluationResponse) => void;
  sessionId?: string | null;
}

export function ChunkReevaluateControl({
  chunkIndex,
  originalState,
  onReevaluation,
  sessionId,
}: ChunkReevaluateControlProps) {
  const [isReevaluating, setIsReevaluating] = React.useState(false);
  const { supportedAgents, supportedAgentsError } = useSupportedAgents();

  const handleReevaluate = async (selectedAgents: Set<string>) => {
    setIsReevaluating(true);

    try {
      const request: ChunkReevaluationRequest = {
        chunkIndex: chunkIndex,
        agentsToRun: Array.from(selectedAgents),
        originalState: originalState,
        sessionId: sessionId ?? null,
      };

      const result = await analysisService.reevaluateChunk(request);
      onReevaluation(result);
    } finally {
      setIsReevaluating(false);
    }
  };

  return (
    <ExpandableControl
      title="Re-evaluate Chunk"
      buttonText="Re-analyze"
      expandedButtonText="Cancel"
      isProcessing={isReevaluating}
      processingText="Re-analyzing..."
      chunkIndex={chunkIndex}
      supportedAgents={supportedAgents}
      supportedAgentsError={supportedAgentsError}
      agentSelectorTitle="Select Agents to Run:"
      backgroundClassName="bg-gray-50"
      footerText="Re-analyze chunk {chunkIndex}"
      actionButtonText="Run Re-analysis"
      onAction={handleReevaluate}
    />
  );
}
