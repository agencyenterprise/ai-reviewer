'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useCallback } from 'react';
import { TabType, tabFromPathname, tabHref } from './constants';

/**
 * Drives a {@link ProjectShell}'s tabs from the URL, one route per tab.
 * `basePath` is the route holding the shell, e.g. `/projects/abc` or `/share/xyz`.
 */
export function useTabRouting(basePath: string) {
  const pathname = usePathname();
  const router = useRouter();

  const activeTab = tabFromPathname(pathname, basePath);

  const onTabChange = useCallback(
    (tab: TabType, hash?: string) => {
      router.push(`${tabHref(basePath, tab)}${hash ?? ''}`);
    },
    [router, basePath],
  );

  return { activeTab, onTabChange };
}
