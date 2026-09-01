export const TABS = ['document-explorer', 'references', 'files', 'analyses', 'peer-review'] as const;

export type TabType = (typeof TABS)[number];

/** The tab shown at a base route, which therefore has no path segment of its own. */
export const ROOT_TAB: TabType = 'document-explorer';

/**
 * Route for a tab under a base path (`/projects/[projectId]` or `/share/[token]`).
 * The root tab lives at the base path itself.
 */
export function tabHref(basePath: string, tab: TabType): string {
  return tab === ROOT_TAB ? basePath : `${basePath}/${tab}`;
}

/** Resolve the active tab from a pathname under `basePath`. */
export function tabFromPathname(pathname: string, basePath: string): TabType {
  const suffix = pathname.slice(basePath.length).replace(/^\//, '').replace(/\/$/, '');
  return TABS.find((tab) => tab === suffix) ?? ROOT_TAB;
}
