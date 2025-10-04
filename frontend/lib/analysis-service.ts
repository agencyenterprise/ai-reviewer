import { AnalysisResults } from '@/components/wizard/types';
import {
  ChunkEvalPackageRequest,
  ChunkReevaluationRequest,
  ChunkReevaluationResponse,
  ClaimSubstantiatorStateOutput,
  DefaultApi,
  EvalPackageRequest,
  SubstantiationWorkflowConfig,
} from '@/lib/generated-api';
import { downloadBlobResponse, generateDefaultTestName } from '@/lib/utils';
import { api } from './api';

interface AnalysisRequest {
  mainDocument: File;
  supportingDocuments?: File[];
  config?: SubstantiationWorkflowConfig;
}

export interface SupportedAgentsResponse {
  supported_agents: string[];
  agent_descriptions: Record<string, string>;
}

class AnalysisService {
  private readonly api: DefaultApi;

  constructor() {
    this.api = api;
  }

  private transformResponse(apiResponse: ClaimSubstantiatorStateOutput): AnalysisResults {
    return {
      status: 'completed',
      fullResults: apiResponse,
    };
  }

  private createErrorResult(error: unknown): AnalysisResults {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';

    return {
      status: 'error',
      error: errorMessage,
    };
  }

  async runClaimSubstantiation(request: AnalysisRequest): Promise<AnalysisResults> {
    try {
      const config = request.config || {};

      // Use OpenAPI client for claim substantiation
      const result = await this.api.runClaimSubstantiationWorkflowApiRunClaimSubstantiationPost({
        mainDocument: request.mainDocument,
        supportingDocuments: request.supportingDocuments || null,
        useToulmin: config.useToulmin,
        runLiteratureReview: config.runLiteratureReview,
        runSuggestCitations: config.runSuggestCitations,
        domain: config.domain || null,
        targetAudience: config.targetAudience || null,
        targetChunkIndices: config.targetChunkIndices?.join(',') || null,
        agentsToRun: config.agentsToRun?.join(',') || null,
        sessionId: config.sessionId || null,
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

  async reevaluateChunk(
    request: ChunkReevaluationRequest & { sessionId?: string | null },
  ): Promise<ChunkReevaluationResponse> {
    try {
      const requestWithSession: ChunkReevaluationRequest = {
        ...request,
        sessionId: request.sessionId,
      };

      return await this.api.reevaluateChunkApiReevaluateChunkPost({
        chunkReevaluationRequest: requestWithSession,
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
        results,
        testName: testName || generateDefaultTestName('eval'),
        description: description || 'Generated from frontend analysis',
      };

      return downloadBlobResponse(() =>
        this.api.generateEvalPackageApiGenerateEvalPackagePostRaw({
          evalPackageRequest: evalRequest,
        }),
      );
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
        results,
        chunkIndex,
        selectedAgents,
        testName: testName || generateDefaultTestName('chunk_eval', chunkIndex.toString()),
        description: description || `Generated from chunk ${chunkIndex} analysis`,
      };

      return downloadBlobResponse(() =>
        this.api.generateChunkEvalPackageApiGenerateChunkEvalPackagePostRaw({
          chunkEvalPackageRequest: evalRequest,
        }),
      );
    } catch (error) {
      console.error('Error generating chunk eval package:', error);
      throw error;
    }
  }
}

export const analysisService = new AnalysisService();

export { AnalysisService };
export type { AnalysisRequest };
