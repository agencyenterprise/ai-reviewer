export interface FileProgress {
  fileName: string;
  progress: number; // 0-100
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
}

export type ProgressCallback = (progress: number) => void;
export type StageChangeCallback = (stage: 'uploading' | 'complete') => void;

export interface ProgressCallbacks {
  onProgress?: ProgressCallback;
  onStageChange?: StageChangeCallback;
}

export class ProgressTracker {
  private currentProgress: number = 0;
  private status: FileProgress['status'] = 'pending';
  private error?: string;

  constructor(private readonly fileName: string = 'Upload') {}

  setProgress(progress: number): FileProgress {
    this.currentProgress = Math.min(100, Math.max(0, progress));
    if (this.status === 'pending' && progress > 0) {
      this.status = 'uploading';
    }
    return this.getState();
  }

  setCompleted(): FileProgress {
    this.currentProgress = 100;
    this.status = 'completed';
    return this.getState();
  }

  setError(error: string): FileProgress {
    this.status = 'error';
    this.error = error;
    return this.getState();
  }

  getState(): FileProgress {
    return {
      fileName: this.fileName,
      progress: this.currentProgress,
      status: this.status,
      error: this.error,
    };
  }
}
