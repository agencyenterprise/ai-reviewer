'use client';

import * as React from 'react';
import { FileText } from 'lucide-react';
import { analysisService, SupportedAgentsResponse } from '@/lib/analysis-service';
import { ClaimSubstantiatorStateOutput } from '@/lib/generated-api';
import { ExpandableControl } from './expandable-control';
import { downloadFile, generateEvalFilename } from '@/lib/file-download';

interface ChunkEvalGeneratorProps {
  chunkIndex: number;
  originalState: ClaimSubstantiatorStateOutput;
  supportedAgents: SupportedAgentsResponse | null;
  supportedAgentsError: string | null;
}

interface OptimizationInfoProps {
  selectedAgents: Set<string>;
}

function OptimizationInfo({ selectedAgents }: OptimizationInfoProps) {
  const agents = Array.from(selectedAgents);
  const needsSupporting = agents.some((agent) => ['references', 'substantiation'].includes(agent));

  const optimization = {
    mainDocument: true,
    supportingDocuments: needsSupporting,
    yamlFiles: agents.length,
  };

  return (
    <div className="text-xs text-blue-600 bg-blue-100 p-2 rounded">
      <div className="font-medium">Package will include:</div>
      <div>• Main document: ✅</div>
      <div>• Supporting docs: {optimization.supportingDocuments ? '✅' : '❌ (not needed)'}</div>
      <div>• YAML files: {optimization.yamlFiles}</div>
    </div>
  );
}

export function ChunkEvalGenerator({
  chunkIndex,
  originalState,
  supportedAgents,
  supportedAgentsError,
}: ChunkEvalGeneratorProps) {
  const [isGenerating, setIsGenerating] = React.useState(false);

  const handleGenerateEval = async (selectedAgents: Set<string>) => {
    setIsGenerating(true);

    try {
      const testName = `chunk_${chunkIndex}_eval_${Date.now()}`;
      const description = `Generated from chunk ${chunkIndex} analysis on ${new Date().toLocaleDateString()}`;

      const blob = await analysisService.generateChunkEvalPackage(
        originalState,
        chunkIndex,
        Array.from(selectedAgents),
        testName,
        description,
      );

      downloadFile({
        filename: generateEvalFilename(testName, chunkIndex),
        blob,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <ExpandableControl
      title="Generate Eval Test"
      buttonText={
        <div className="flex items-center">
          <FileText className="w-3 h-3 mr-1" />
          Create Eval
        </div>
      }
      expandedButtonText="Cancel"
      isProcessing={isGenerating}
      processingText="Generating..."
      chunkIndex={chunkIndex}
      supportedAgents={supportedAgents}
      supportedAgentsError={supportedAgentsError}
      agentSelectorTitle="Select Agents for Eval:"
      backgroundClassName="bg-blue-50"
      footerText="Optimized package for chunk {chunkIndex}"
      actionButtonText="Download Eval Package"
      onAction={handleGenerateEval}
    >
      {(selectedAgents) => (selectedAgents.size > 0 ? <OptimizationInfo selectedAgents={selectedAgents} /> : null)}
    </ExpandableControl>
  );
}
