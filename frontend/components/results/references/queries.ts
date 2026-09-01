import { formatFileSize } from '@/components/analysis-form/utils';
import { composeReferences } from '@/lib/composed-references';
import { MatchSource, ProjectDetailed, ReferenceFetchStatus, WorkflowRunType } from '@/lib/generated-api';
import { getWorkflowRunByType } from '@/lib/workflow-state';
import { useMemo } from 'react';
import { ReferenceReviewItem } from './types';

export function useReferenceReviewReferences(projectDetail: ProjectDetailed | undefined) {
  const files = useMemo(() => projectDetail?.files ?? [], [projectDetail?.files]);
  const workflowDetails = useMemo(() => projectDetail?.workflow_runs ?? [], [projectDetail?.workflow_runs]);

  const { referenceExtraction, referenceFileMatching, referenceDownloader } = useMemo(() => {
    return {
      referenceExtraction: getWorkflowRunByType(workflowDetails, WorkflowRunType.ReferenceExtraction),
      referenceFileMatching: getWorkflowRunByType(workflowDetails, WorkflowRunType.ReferenceFileMatching),
      referenceDownloader: getWorkflowRunByType(workflowDetails, WorkflowRunType.ReferenceDownloader),
    };
  }, [workflowDetails]);

  // Compose references from extraction and file matching states
  const composedReferences = useMemo(
    () =>
      composeReferences(referenceExtraction?.state?.extracted_references, referenceFileMatching?.state?.matches, files),
    [referenceExtraction?.state?.extracted_references, referenceFileMatching?.state?.matches, files],
  );

  const references = useMemo(() => {
    if (!referenceExtraction) {
      return [];
    }

    return composedReferences.map((item, index): ReferenceReviewItem => {
      const matchedFile = item.file_id ? files?.find((file) => file.id === item.file_id) : undefined;
      const fetchedReference = referenceDownloader?.state?.fetched_references?.find(
        (ref) => ref.reference_id === item.id,
      );

      // Hide fetch results when the file was manually uploaded by the user — the fetch outcome is
      // irrelevant once a user-uploaded source is in place. Otherwise always surface the fetch
      // result (including "Not Found" / errored outcomes) so users can see why no source is attached.
      const shouldShowFetchedResult = !!fetchedReference && item.source !== MatchSource.ManualUpload;

      return {
        id: item.id,
        index,
        text: item.text,
        status:
          fetchedReference?.status === ReferenceFetchStatus.Pending
            ? 'fetching'
            : matchedFile
              ? 'matched'
              : 'unmatched',
        matchedFile: matchedFile
          ? {
              id: matchedFile.id,
              name: matchedFile.file_name,
              size: formatFileSize(matchedFile.file_size),
            }
          : null,
        source: item.source,
        fetchResult: shouldShowFetchedResult ? fetchedReference : null,
      };
    });
  }, [composedReferences, files, referenceExtraction, referenceDownloader]);

  return references;
}
