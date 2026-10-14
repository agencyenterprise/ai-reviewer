import type { DownloadOptions } from '@/lib/file-download';
import type { AnnotationSetStats, ExportAnnotationsApiAdminAnnotationsExportGetResponse } from '@/lib/generated-api';

/** The set whose items are on screen: the one the admin picked, else the first set listed. */
export function currentSetSlug(sets: AnnotationSetStats[] | undefined, selected: string | null): string | null {
  return selected ?? sets?.[0]?.slug ?? null;
}

/** One dated JSON file holding every set's results. */
export function annotationsExportFile(
  sets: ExportAnnotationsApiAdminAnnotationsExportGetResponse,
  now: Date,
): DownloadOptions {
  return {
    filename: `annotations-${now.toISOString().slice(0, 10)}.json`,
    blob: new Blob([JSON.stringify(sets, null, 2)], { type: 'application/json' }),
  };
}
