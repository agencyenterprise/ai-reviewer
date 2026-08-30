'use client';

import { useProjectView } from '@/components/results/project-view-context';
import { FilesTabV2 } from './files/files-tab';

/** The v2 files tab as a tab panel, taking its project from the shell. */
export function FilesV2Panel() {
  const { projectDetail, readOnly, onRevisionCreated } = useProjectView();

  return <FilesTabV2 projectDetail={projectDetail} readOnly={readOnly} onRevisionCreated={onRevisionCreated} />;
}
