export const TABS = ['summary', 'document-explorer', 'files', 'citations', 'references', 'literature_review'] as const;

export type TabType = (typeof TABS)[number];

export const TAB_LABELS: Record<TabType, string> = {
  summary: 'Summary',
  'document-explorer': 'Explorer',
  files: 'Files',
  citations: 'Citations',
  references: 'References',
  literature_review: 'Literature Review',
};
