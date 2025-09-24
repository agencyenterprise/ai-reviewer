'use client';

import * as React from 'react';
import { Button } from '@/components/ui/button';
import { SupportedAgentsResponse } from '@/lib/analysis-service';

interface AgentSelectorProps {
  supportedAgents: SupportedAgentsResponse | null;
  supportedAgentsError: string | null;
  selectedAgents: Set<string>;
  onAgentToggle: (agentId: string, checked: boolean) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  disabled?: boolean;
  title?: string;
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

export function AgentSelector({
  supportedAgents,
  supportedAgentsError,
  selectedAgents,
  onAgentToggle,
  onSelectAll,
  onDeselectAll,
  disabled = false,
  title = 'Select Agents:',
}: AgentSelectorProps) {
  if (supportedAgentsError) {
    return <div className="text-sm text-red-500">Error: {supportedAgentsError}</div>;
  }

  if (!supportedAgents) {
    return <div className="text-sm text-gray-500">Loading agents...</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">{title}</span>
        <div className="space-x-2">
          <Button variant="ghost" size="sm" onClick={onSelectAll} className="text-xs h-6 px-2" disabled={disabled}>
            All
          </Button>
          <Button variant="ghost" size="sm" onClick={onDeselectAll} className="text-xs h-6 px-2" disabled={disabled}>
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
            onChange={(checked) => onAgentToggle(agentId, checked)}
            disabled={disabled}
          />
        ))}
      </div>

      <div className="mt-2">
        <span className="text-xs text-gray-500">
          {selectedAgents.size} of {supportedAgents.supported_agents.length} agents selected
        </span>
      </div>
    </div>
  );
}
