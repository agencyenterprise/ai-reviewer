import { AnalysisApi, Configuration, EvaluationApi, FeedbackApi, HealthApi, WorkflowsApi } from './generated-api';

export const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const config = new Configuration({
  basePath: apiUrl,
});

export const analysisApi = new AnalysisApi(config);
export const evaluationApi = new EvaluationApi(config);
export const feedbackApi = new FeedbackApi(config);
export const healthApi = new HealthApi(config);
export const workflowsApi = new WorkflowsApi(config);
