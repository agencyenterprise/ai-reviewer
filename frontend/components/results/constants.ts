export const TABS = ['document-explorer', 'summary', 'references', 'files', 'analyses', 'peer-review'] as const;

export type TabType = (typeof TABS)[number];
