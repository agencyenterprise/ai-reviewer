import { PanePreview } from '@/components/addin/preview/pane-preview';
import { Suspense } from 'react';

/**
 * The Word pane in a browser, with Word and the add-in's API stood in for
 * (`components/addin/preview/`). Served everywhere: it only talks to itself.
 */
export default function AddinPreviewPage() {
  return (
    <Suspense>
      <PanePreview />
    </Suspense>
  );
}
