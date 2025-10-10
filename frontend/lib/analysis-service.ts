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
import { api, apiUrl } from './api';

interface AnalysisRequest {
  mainDocument: File;
  supportingDocuments?: File[];
  config?: SubstantiationWorkflowConfig;
}

export interface SupportedAgentsResponse {
  supported_agents: string[];
  agent_descriptions: Record<string, string>;
}

/**
 * Response from starting an analysis workflow
 * Note: This should match the backend StartAnalysisResponse model
 */
export interface StartAnalysisResponse {
  workflow_run_id: string;
  session_id: string;
  message: string;
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

  /**
   * Start analysis with upload progress tracking.
   *
   * Note: This method bypasses the OpenAPI client to support
   * XMLHttpRequest progress events. All other endpoints use
   * the generated client for type safety.
   */
  async startAnalysis(
    request: AnalysisRequest,
    onProgress?: (progress: number) => void,
  ): Promise<StartAnalysisResponse> {
    return new Promise((resolve, reject) => {
      try {
        const config = request.config || {};

        const formData = new FormData();
        formData.append('main_document', request.mainDocument);

        if (request.supportingDocuments) {
          request.supportingDocuments.forEach((file) => {
            formData.append('supporting_documents', file);
          });
        }

        // Add config parameters
        if (config.useToulmin !== undefined) formData.append('use_toulmin', String(config.useToulmin));
        if (config.runLiteratureReview !== undefined)
          formData.append('run_literature_review', String(config.runLiteratureReview));
        if (config.runSuggestCitations !== undefined)
          formData.append('run_suggest_citations', String(config.runSuggestCitations));
        if (config.domain) formData.append('domain', config.domain);
        if (config.targetAudience) formData.append('target_audience', config.targetAudience);
        if (config.sessionId) formData.append('session_id', config.sessionId);

        // Use XMLHttpRequest for upload progress tracking
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable && onProgress) {
            const percentComplete = (event.loaded / event.total) * 100;
            onProgress(percentComplete);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const response = JSON.parse(xhr.responseText);
              resolve(response);
            } catch (e) {
              reject(new Error('Failed to parse response'));
            }
          } else {
            reject(new Error(`HTTP error! status: ${xhr.status}`));
          }
        });

        xhr.addEventListener('error', () => {
          reject(new Error('Network error occurred'));
        });

        xhr.addEventListener('abort', () => {
          reject(new Error('Upload aborted'));
        });

        xhr.open('POST', `${apiUrl}/api/start-analysis`);
        xhr.send(formData);
      } catch (error) {
        console.error('Error starting analysis:', error);
        reject(error);
      }
    });
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
