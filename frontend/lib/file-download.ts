/**
 * Utilities for file download operations.
 */

export interface DownloadOptions {
  filename: string;
  blob: Blob;
}

/**
 * Triggers a download of a blob file in the browser.
 */
export function downloadFile({ filename, blob }: DownloadOptions): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');

  link.href = url;
  link.download = filename;

  // Temporarily add to DOM and trigger click
  document.body.appendChild(link);
  link.click();

  // Clean up
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Generates a filename with timestamp for eval packages.
 */
export function generateEvalFilename(testName: string, chunkIndex?: number): string {
  const suffix = chunkIndex !== undefined ? `_chunk_${chunkIndex}` : '';
  return `${testName}${suffix}_eval_package.zip`;
}
