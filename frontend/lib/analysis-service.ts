import { AnalysisResults } from '@/components/wizard/types';
import {
  ClaimSubstantiatorStateOutput,
  Configuration,
  DefaultApi,
  RunClaimSubstantiationWorkflowApiRunClaimSubstantiationPostRequest,
  ChunkReevaluationRequest,
  ChunkReevaluationResponse,
} from '@/lib/generated-api';

interface AnalysisRequest {
  mainDocument: File;
  supportingDocuments?: File[];
  domain?: string;
  targetAudience?: string;
}

export interface SupportedAgentsResponse {
  supported_agents: string[];
  agent_descriptions: Record<string, string>;
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

  private transformResponse(apiResponse: ClaimSubstantiatorStateOutput): AnalysisResults {
    return {
      status: 'completed',
      fullResults: apiResponse as unknown as ClaimSubstantiatorStateOutput,
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
        useToulmin: request.useToulmin,
        domain: request.domain,
        targetAudience: request.targetAudience,
      });

      return this.transformResponse(result);
    } catch (error) {
      console.error('Error calling claim substantiation API:', error);
      return this.createErrorResult(error);
    }
  }

  async getSupportedAgents(): Promise<SupportedAgentsResponse> {
    try {
      return await this.api.getSupportedAgentsApiSupportedAgentsGet();
    } catch (error) {
      console.error('Error fetching supported agents:', error);
      throw error;
    }
  }

  async reevaluateChunk(request: ChunkReevaluationRequest): Promise<ChunkReevaluationResponse> {
    try {
      return await this.api.reevaluateChunkApiReevaluateChunkPost({
        chunkReevaluationRequest: request,
      });
    } catch (error) {
      console.error('Error re-evaluating chunk:', error);
      throw error;
    }
  }
}

export const analysisService = new AnalysisService();

export { AnalysisService };
export type { AnalysisRequest };
