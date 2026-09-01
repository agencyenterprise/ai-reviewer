'use client';

import { useCallback, useSyncExternalStore } from 'react';

/**
 * Whether a media query currently matches, kept in sync with the browser.
 *
 * The server has no viewport, so it answers `wide` and the client corrects on
 * hydration if it is wrong. That bias is deliberate: this view is used on
 * desktop most of the time, and guessing narrow would flash the layout on
 * nearly every load.
 */
export function useMediaQuery(query: string, serverFallback = true): boolean {
  const subscribe = useCallback(
    (onChange: () => void) => {
      const list = window.matchMedia(query);
      list.addEventListener('change', onChange);
      return () => list.removeEventListener('change', onChange);
    },
    [query],
  );

  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia(query).matches,
    () => serverFallback,
  );
}

/** The widths the project view's panes appear at, matching Tailwind's xl and lg. */
export const WIDE_ENOUGH_FOR_RAIL = '(min-width: 80rem)';
export const WIDE_ENOUGH_FOR_PANE = '(min-width: 64rem)';
