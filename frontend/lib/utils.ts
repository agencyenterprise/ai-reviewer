import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function generateDefaultTestName(prefix: string, suffix?: string): string {
  const timestamp = Date.now();
  return suffix ? `${prefix}_${suffix}_${timestamp}` : `${prefix}_${timestamp}`;
}

export async function downloadBlobResponse(apiCall: () => Promise<{ raw: Response }>): Promise<Blob> {
  const apiResponse = await apiCall();
  return await apiResponse.raw.blob();
}
