'use client';

import * as React from 'react';
import { Button } from '@/components/ui/button';
import { extendedAnalysisService, ChunkReevaluationRequest, SupportedAgentsResponse } from '@/lib/analysis-service';
import { ClaimSubstantiatorState } from '@/lib/generated-api';

interface ChunkReevaluateControlProps {
  chunkIndex: number;
  originalState: ClaimSubstantiatorState;
  onReevaluation: (chunkIndex: number, updatedResults: Record<string, unknown>) => void;
}

interface AgentCheckboxProps {
  agentId: string;
  agentDescription: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

function AgentCheckbox({ agentId, agentDescription, checked, onChange, disabled }: AgentCheckboxProps) {
  return (
    <label className="flex items-center space-x-2 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
      />
      <div className="flex-1">
        <span className="text-sm font-medium capitalize">{agentId}</span>
        <p className="text-xs text-gray-500">{agentDescription}</p>
      </div>
    </label>
  );
}

export function ChunkReevaluateControl({ chunkIndex, originalState, onReevaluation }: ChunkReevaluateControlProps) {
  const [supportedAgents, setSupportedAgents] = React.useState<SupportedAgentsResponse | null>(null);
  const [selectedAgents, setSelectedAgents] = React.useState<Set<string>>(new Set());
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [isReevaluating, setIsReevaluating] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Load supported agents on mount
  React.useEffect(() => {
    const loadSupportedAgents = async () => {
      try {
        const agents = await extendedAnalysisService.getSupportedAgents();
        setSupportedAgents(agents);
        // Pre-select all agents by default
        setSelectedAgents(new Set(agents.supported_agents));
      } catch (error) {
        console.error('Failed to load supported agents:', error);
        setError('Failed to load available agents');
      }
    };

    loadSupportedAgents();
  }, []);

  const handleAgentToggle = (agentId: string, checked: boolean) => {
    const newSelected = new Set(selectedAgents);
    if (checked) {
      newSelected.add(agentId);
    } else {
      newSelected.delete(agentId);
    }
    setSelectedAgents(newSelected);
  };

  const handleReevaluate = async () => {
    if (selectedAgents.size === 0) {
      setError('Please select at least one agent');
      return;
    }

    setIsReevaluating(true);
    setError(null);

    try {
      const request: ChunkReevaluationRequest = {
        chunk_index: chunkIndex,
        agents_to_run: Array.from(selectedAgents),
        original_state: originalState,
      };

      const result = await extendedAnalysisService.reevaluateChunk(request);
      onReevaluation(chunkIndex, result.updated_results);
      setIsExpanded(false);
    } catch (error) {
      console.error('Re-evaluation failed:', error);
      setError(error instanceof Error ? error.message : 'Re-evaluation failed');
    } finally {
      setIsReevaluating(false);
    }
  };

  const handleSelectAll = () => {
    if (supportedAgents) {
      setSelectedAgents(new Set(supportedAgents.supported_agents));
    }
  };

  const handleDeselectAll = () => {
    setSelectedAgents(new Set());
  };

  if (!supportedAgents) {
    return <div className="text-sm text-gray-500">Loading re-evaluation options...</div>;
  }

  return (
    <div className="border-t pt-3 mt-3">
      <div className="flex items-center justify-between">
        <h5 className="text-sm font-medium text-gray-700">Re-evaluate Chunk</h5>
        <Button variant="outline" size="sm" onClick={() => setIsExpanded(!isExpanded)} disabled={isReevaluating}>
          {isExpanded ? 'Cancel' : 'Re-analyze'}
        </Button>
      </div>

      {isExpanded && (
        <div className="mt-3 p-3 bg-gray-50 rounded-md space-y-3">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Select Agents to Run:</span>
              <div className="space-x-2">
                <Button variant="ghost" size="sm" onClick={handleSelectAll} className="text-xs h-6 px-2">
                  All
                </Button>
                <Button variant="ghost" size="sm" onClick={handleDeselectAll} className="text-xs h-6 px-2">
                  None
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              {supportedAgents.supported_agents.map((agentId) => (
                <AgentCheckbox
                  key={agentId}
                  agentId={agentId}
                  agentDescription={supportedAgents.agent_descriptions[agentId] || ''}
                  checked={selectedAgents.has(agentId)}
                  onChange={(checked) => handleAgentToggle(agentId, checked)}
                  disabled={isReevaluating}
                />
              ))}
            </div>
          </div>

          {error && <div className="text-sm text-red-600 bg-red-50 p-2 rounded">{error}</div>}

          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">
              {selectedAgents.size} of {supportedAgents.supported_agents.length} agents selected
            </span>
            <Button onClick={handleReevaluate} disabled={isReevaluating || selectedAgents.size === 0} size="sm">
              {isReevaluating ? 'Re-analyzing...' : 'Run Re-analysis'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
