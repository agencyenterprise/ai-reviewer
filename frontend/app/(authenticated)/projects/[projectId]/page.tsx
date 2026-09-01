'use client';

import { DocumentExplorerPanel } from '@/components/results/document-explorer-panel';

/** The document explorer is the root tab, so existing links to a project land on it. */
export default function Page() {
  return <DocumentExplorerPanel />;
}
