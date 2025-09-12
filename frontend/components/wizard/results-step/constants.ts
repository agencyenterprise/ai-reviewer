export const TABS = ['summary', 'files', 'chunks', 'claims', 'citations', 'references'] as const

export type TabType = typeof TABS[number]

export const TAB_LABELS: Record<TabType, string> = {
    summary: 'Summary',
    files: 'Files',
    chunks: 'Chunks',
    claims: 'Claims',
    citations: 'Citations',
    references: 'References',
}
