export const TABS = ['summary', 'claims', 'citations', 'references'] as const

export type TabType = typeof TABS[number]

export const TAB_LABELS: Record<TabType, string> = {
    summary: 'Summary',
    claims: 'Claims',
    citations: 'Citations',
    references: 'References'
}
