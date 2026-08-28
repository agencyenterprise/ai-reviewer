'use client';

import { useProjectView } from '@/components/results/project-view-context';
import { ReferencesTabV2 } from './references/references-tab';

/** The v2 references tab as a tab panel, taking its project from the shell. */
export function ReferencesV2Panel() {
  const { projectDetail, readOnly } = useProjectView();

  return <ReferencesTabV2 projectDetail={projectDetail} readOnly={readOnly} />;
}
