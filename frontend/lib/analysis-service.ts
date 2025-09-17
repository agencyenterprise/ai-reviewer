import { AnalysisResults } from '@/components/wizard/types';
import {
  ClaimSubstantiatorState,
  Configuration,
  DefaultApi,
  RunClaimSubstantiationWorkflowApiRunClaimSubstantiationPostRequest,
} from '@/lib/generated-api';

interface AnalysisRequest {
  mainDocument: File;
  supportingDocuments?: File[];
}

class AnalysisService {
  private readonly apiUrl: string;
  private readonly api: DefaultApi;

  constructor() {
    this.apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    this.api = new DefaultApi(
      new Configuration({
        basePath: this.apiUrl,
      }),
    );
  }

  private transformResponse(apiResponse: ClaimSubstantiatorState): AnalysisResults {
    return {
      status: 'completed',
      fullResults: apiResponse as unknown as ClaimSubstantiatorState,
    };
  }

  private createErrorResult(error: unknown): AnalysisResults {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';

    return {
      status: 'error',
      error: errorMessage,
    };
  }

  async runClaimSubstantiation(
    request: RunClaimSubstantiationWorkflowApiRunClaimSubstantiationPostRequest,
  ): Promise<AnalysisResults> {
    try {
      const result = await this.api.runClaimSubstantiationWorkflowApiRunClaimSubstantiationPost({
        mainDocument: request.mainDocument,
        supportingDocuments: request.supportingDocuments,
      });

      return this.transformResponse(result);
    } catch (error) {
      console.error('Error calling claim substantiation API:', error);
      return this.createErrorResult(error);
    }
  }
}

export const analysisService = new AnalysisService();

// Chunk re-evaluation types and interfaces
export interface ChunkReevaluationRequest {
  chunk_index: number;
  agents_to_run: string[];
  original_state: ClaimSubstantiatorState;
}

export interface ChunkReevaluationResponse {
  chunk_index: number;
  chunk_content: string;
  updated_results: Record<string, unknown>;
  agents_run: string[];
  processing_time_ms?: number;
}

export interface SupportedAgentsResponse {
  supported_agents: string[];
  agent_descriptions: Record<string, string>;
}

export class ExtendedAnalysisService extends AnalysisService {
  private readonly baseUrl: string;

  constructor() {
    super();
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  async getSupportedAgents(): Promise<SupportedAgentsResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/supported-agents`);
      if (!response.ok) {
        throw new Error(`Failed to fetch supported agents: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching supported agents:', error);
      throw error;
    }
  }

  async reevaluateChunk(request: ChunkReevaluationRequest): Promise<ChunkReevaluationResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/reevaluate-chunk`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `Request failed with status ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error re-evaluating chunk:', error);
      throw error;
    }
  }
}

export const extendedAnalysisService = new ExtendedAnalysisService();

export { AnalysisService };
export type { AnalysisRequest };
