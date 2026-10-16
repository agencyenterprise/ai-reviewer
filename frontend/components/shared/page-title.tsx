'use client';

import { useEffect } from 'react';

const DEFAULT_TITLE = 'Draft Detective';

/**
 * Names the browser tab after what is on screen.
 *
 * Route metadata cannot do it: these pages are client components whose subject
 * arrives from a query, which `generateMetadata` on the server has no way to
 * read. Nor can a rendered `<title>` — React hoists one into the head, but the
 * App Router rewrites the head on every client navigation and drops it, taking
 * the app-wide default with it, so switching tabs left the tab unnamed.
 *
 * Setting `document.title` is a side effect on something React does not own, so
 * an effect is the right tool here rather than the exception. Writing it once is
 * not enough: the shell stays mounted across tab switches, and since Next 16 the
 * router inserts the route's `<title>` after this effect has run. So the effect
 * watches the head and writes the title back whenever the router replaces it.
 */
export function PageTitle({ title }: { title: string }) {
  useEffect(() => {
    // `document.title` reads back with whitespace collapsed, so compare against that
    // form; otherwise a title with a double space would rewrite itself forever.
    const trimmed = title.replace(/\s+/g, ' ').trim();
    const wanted = trimmed ? `${trimmed} · ${DEFAULT_TITLE}` : DEFAULT_TITLE;
    const apply = () => {
      if (document.title !== wanted) document.title = wanted;
    };

    apply();
    const observer = new MutationObserver(apply);
    observer.observe(document.head, { childList: true, subtree: true, characterData: true });

    return () => {
      observer.disconnect();
      document.title = DEFAULT_TITLE;
    };
  }, [title]);

  return null;
}
