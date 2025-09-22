import { AnalysisResults } from '@/components/wizard/types';
import {
  ClaimSubstantiatorStateOutput,
  Configuration,
  DefaultApi,
  RunClaimSubstantiationWorkflowApiRunClaimSubstantiationPostRequest,
  ChunkReevaluationRequest,
  ChunkReevaluationResponse,
  EvalPackageRequest,
  ChunkEvalPackageRequest,
} from '@/lib/generated-api';

interface AnalysisRequest {
  mainDocument: File;
  supportingDocuments?: File[];
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

  async generateEvalPackage(
    results: ClaimSubstantiatorStateOutput,
    testName?: string,
    description?: string,
  ): Promise<Blob> {
    try {
      const evalRequest: EvalPackageRequest = {
        results: results as any,
        testName: testName || `eval_${Date.now()}`,
        description: description || 'Generated from frontend analysis',
      };

      const apiResponse = await this.api.generateEvalPackageApiGenerateEvalPackagePostRaw({
        evalPackageRequest: evalRequest,
      });

      const response = apiResponse.raw;
      return await response.blob();
    } catch (error) {
      console.error('Error generating eval package:', error);
      throw error;
    }
  }

  async generateChunkEvalPackage(
    results: ClaimSubstantiatorStateOutput,
    chunkIndex: number,
    selectedAgents: string[],
    testName?: string,
    description?: string,
  ): Promise<Blob> {
    try {
      const evalRequest: ChunkEvalPackageRequest = {
        results: results as any,
        chunkIndex: chunkIndex,
        selectedAgents: selectedAgents,
        testName: testName || `chunk_eval_${chunkIndex}_${Date.now()}`,
        description: description || `Generated from chunk ${chunkIndex} analysis`,
      };

      const apiResponse = await this.api.generateChunkEvalPackageApiGenerateChunkEvalPackagePostRaw({
        chunkEvalPackageRequest: evalRequest,
      });

      const response = apiResponse.raw;
      return await response.blob();
    } catch (error) {
      console.error('Error generating chunk eval package:', error);
      throw error;
    }
  }
}

export const analysisService = new AnalysisService();

export { AnalysisService };
export type { AnalysisRequest };
