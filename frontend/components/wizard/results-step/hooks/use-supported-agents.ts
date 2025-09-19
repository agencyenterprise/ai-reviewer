import * as React from 'react';
import { analysisService, SupportedAgentsResponse } from '@/lib/analysis-service';

interface UseSupportedAgentsReturn {
  supportedAgents: SupportedAgentsResponse | null;
  supportedAgentsError: string | null;
  isLoading: boolean;
}

export function useSupportedAgents(): UseSupportedAgentsReturn {
  const [supportedAgents, setSupportedAgents] = React.useState<SupportedAgentsResponse | null>(null);
  const [supportedAgentsError, setSupportedAgentsError] = React.useState<string | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    const loadSupportedAgents = async () => {
      try {
        setIsLoading(true);
        setSupportedAgentsError(null);
        const agents = await analysisService.getSupportedAgents();
        setSupportedAgents(agents);
      } catch (error) {
        console.error('Failed to load supported agents:', error);
        setSupportedAgentsError('Failed to load available agents');
      } finally {
        setIsLoading(false);
      }
    };

    loadSupportedAgents();
  }, []);

  return {
    supportedAgents,
    supportedAgentsError,
    isLoading,
  };
}
