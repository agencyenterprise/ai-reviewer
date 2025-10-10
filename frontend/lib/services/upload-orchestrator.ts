/**
 * Upload orchestration service - handles file validation and upload coordination
 */

import { MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB } from '../constants';
import { ProgressCallbacks, ProgressTracker } from './progress-tracker';
import { analysisService, AnalysisRequest, StartAnalysisResponse } from '../analysis-service';

export interface ValidationError {
  fileName: string;
  error: string;
}

export interface ValidationResult {
  valid: boolean;
  errors?: ValidationError[];
}

/**
 * Orchestrates file uploads with validation and progress tracking
 */
export class UploadOrchestrator {
  /**
   * Validate files before upload
   */
  validateFiles(files: File[]): ValidationResult {
    const oversized = files.filter((f) => f.size > MAX_FILE_SIZE_BYTES);

    if (oversized.length > 0) {
      return {
        valid: false,
        errors: oversized.map((f) => ({
          fileName: f.name,
          error: `File exceeds ${MAX_FILE_SIZE_MB}MB limit (${(f.size / 1024 / 1024).toFixed(1)}MB)`,
        })),
      };
    }

    return { valid: true };
  }

  /**
   * Format validation errors as a user-friendly message
   */
  formatValidationErrors(errors: ValidationError[]): string {
    const fileList = errors.map((e) => `${e.fileName}: ${e.error}`).join('\n');
    return `File validation failed:\n${fileList}`;
  }

  /**
   * Start analysis with progress tracking
   */
  async startAnalysisWithProgress(
    request: AnalysisRequest,
    callbacks: ProgressCallbacks,
  ): Promise<StartAnalysisResponse> {
    const tracker = new ProgressTracker('Uploading files');

    try {
      // Notify upload stage started
      callbacks.onStageChange?.('uploading');

      // Start upload with progress tracking
      const response = await analysisService.startAnalysis(request, (progress) => {
        const state = tracker.setProgress(progress);
        callbacks.onProgress?.(state.progress);
      });

      // Mark complete
      tracker.setCompleted();
      callbacks.onProgress?.(100);
      callbacks.onStageChange?.('complete');

      return response;
    } catch (error) {
      // Track error
      tracker.setError(error instanceof Error ? error.message : 'Upload failed');
      throw error;
    }
  }
}

export const uploadOrchestrator = new UploadOrchestrator();
