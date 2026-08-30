import { ReferenceFetchConclusion, ReferenceFetchResult, ReferenceFetchStatus } from '@/lib/generated-api';
import { formatReferenceError } from '@/lib/utils';

const CONCLUSION: Record<ReferenceFetchConclusion, { label: string; className: string }> = {
  [ReferenceFetchConclusion.SourceFound]: { label: 'Source found', className: 'text-green-700 dark:text-green-400' },
  [ReferenceFetchConclusion.SourceFoundButNotAccessible]: {
    label: 'Found, but not readable',
    className: 'text-amber-700 dark:text-amber-400',
  },
  [ReferenceFetchConclusion.SourceNotFound]: { label: 'Not found on the web', className: 'text-muted-foreground' },
};

/**
 * Reads a web fetch's result into the parts the detail pane shows: what came of
 * it, why, and where it looked. Null while the fetch is still running, or when
 * the workflow reported nothing to say.
 */
export function readFetchOutcome(fetchResult: ReferenceFetchResult) {
  if (fetchResult.status === ReferenceFetchStatus.Pending) return null;

  const failed = fetchResult.status === ReferenceFetchStatus.Error || fetchResult.error != null;
  const conclusion = fetchResult.result?.final_conclusion;
  const outcome = failed
    ? { label: 'Fetch failed', className: 'text-red-700 dark:text-red-400' }
    : conclusion
      ? CONCLUSION[conclusion]
      : null;
  if (!outcome) return null;

  return {
    outcome,
    detail: failed ? formatReferenceError(fetchResult.error) : fetchResult.result?.inaccessibility_reason,
    reasoning: fetchResult.result?.reasoning,
    sourceUrl: fetchResult.result?.source_url,
  };
}
