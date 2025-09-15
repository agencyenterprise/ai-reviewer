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

export { AnalysisService };
export type { AnalysisRequest };
