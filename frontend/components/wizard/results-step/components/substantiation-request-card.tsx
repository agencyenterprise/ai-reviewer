'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Settings, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { SubstantiationWorkflowConfig } from '@/lib/generated-api';

export interface SubstantiationRequestCardProps {
  request: SubstantiationWorkflowConfig;
  className?: string;
}

function ConfigItem({
  label,
  value,
  enabled = true,
}: {
  label: string;
  value: string | boolean | number;
  enabled?: boolean;
}) {
  const Icon = enabled ? CheckCircle : XCircle;
  const colorClass = enabled ? 'text-green-600' : 'text-red-600';
  const bgClass = enabled ? 'bg-green-50' : 'bg-red-50';
  const borderClass = enabled ? 'border-green-200' : 'border-red-200';

  return (
    <div className={cn('p-3 rounded-md border-l-4', bgClass, borderClass)}>
      <div className="flex items-center gap-2">
        <Icon className={cn('h-4 w-4', colorClass)} />
        <span className="text-sm font-medium text-gray-700">{label}:</span>
        <Badge
          variant={enabled ? 'default' : 'destructive'}
          className={cn('text-xs', enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800')}
        >
          {typeof value === 'boolean' ? (value ? 'Enabled' : 'Disabled') : String(value)}
        </Badge>
      </div>
    </div>
  );
}

function WorkflowConfigDisplay({ config }: { config: SubstantiationWorkflowConfig }) {
  return (
    <div className="space-y-3">
      <h4 className="font-medium text-gray-900 mb-3">Workflow Configuration</h4>

      <div className="space-y-2">
        <ConfigItem
          label="Toulmin Analysis"
          value={config.useToulmin ? 'Enabled' : 'Disabled'}
          enabled={config.useToulmin}
        />

        <ConfigItem
          label="Target Chunks"
          value={config.targetChunkIndices ? `${config.targetChunkIndices.length} selected` : 'All chunks'}
          enabled={!!config.targetChunkIndices}
        />

        <ConfigItem
          label="Agents to Run"
          value={config.agentsToRun ? config.agentsToRun.join(', ') : 'All agents'}
          enabled={!!config.agentsToRun}
        />

        <ConfigItem label="Domain" value={config.domain || 'Not specified'} enabled={!!config.domain} />

        <ConfigItem
          label="Target Audience"
          value={config.targetAudience || 'Not specified'}
          enabled={!!config.targetAudience}
        />

        <ConfigItem label="Session ID" value={config.sessionId || 'Not specified'} enabled={!!config.sessionId} />
      </div>

      {/* Additional configuration details */}
      <div className="mt-4 p-3 bg-gray-50 rounded-md border-l-4 border-gray-400">
        <div className="flex items-center gap-2 mb-2">
          <AlertCircle className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Configuration Summary</span>
        </div>
        <div className="text-sm text-gray-600 space-y-1">
          <p>
            • <strong>Configuration:</strong> {config.useToulmin ? 'Toulmin analysis enabled' : 'Standard analysis'}
          </p>
          <p>
            • <strong>Workflow Type:</strong> Claim Substantiation Analysis
          </p>
          <p>
            • <strong>Analysis Scope:</strong>{' '}
            {config.useToulmin
              ? 'Full argument analysis with substantiation'
              : 'Basic claim extraction and substantiation'}
          </p>
        </div>
      </div>
    </div>
  );
}

export function SubstantiationRequestCard({ request, className }: SubstantiationRequestCardProps) {
  const config = request;
  const hasToulmin = config.useToulmin;
  const hasSpecificChunks = !!config.targetChunkIndices;
  const hasSpecificAgents = !!config.agentsToRun;
  const hasDomain = !!config.domain;
  const hasAudience = !!config.targetAudience;
  const hasSession = !!config.sessionId;

  const configuredOptions = [
    hasToulmin,
    hasSpecificChunks,
    hasSpecificAgents,
    hasDomain,
    hasAudience,
    hasSession,
  ].filter(Boolean).length;

  const isFullyConfigured = configuredOptions >= 4;
  const hasMinimalConfig = configuredOptions >= 1;

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <div className="p-1.5 rounded-full bg-blue-100">
            <Settings className="h-4 w-4 text-blue-600" />
          </div>
          Substantiation Request
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Main Configuration Status */}
        <div className="bg-gray-50 p-4 rounded-md border-l-4 border-gray-400">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Configuration Status:</span>
              <Badge
                variant={isFullyConfigured ? 'default' : hasMinimalConfig ? 'secondary' : 'destructive'}
                className={cn(
                  'font-medium',
                  isFullyConfigured
                    ? 'bg-green-100 text-green-800 hover:bg-green-200'
                    : hasMinimalConfig
                      ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                      : 'bg-red-100 text-red-800 hover:bg-red-200',
                )}
              >
                {isFullyConfigured
                  ? 'Fully Configured'
                  : hasMinimalConfig
                    ? 'Partially Configured'
                    : 'Minimal Configuration'}
              </Badge>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Options Configured:</span>
              <Badge variant="outline" className="text-xs">
                {configuredOptions}/6
              </Badge>
            </div>
          </div>
        </div>

        {/* Detailed Configuration */}
        <WorkflowConfigDisplay config={config} />
      </CardContent>
    </Card>
  );
}
