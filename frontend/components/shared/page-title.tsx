'use client';

import { usePathname } from 'next/navigation';
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
 * an effect is the right tool here rather than the exception. It is keyed on the
 * path as well as the title: the shell stays mounted across tab switches, and
 * the title has to be written again after each one rewrites the head.
 */
export function PageTitle({ title }: { title: string }) {
  const pathname = usePathname();

  useEffect(() => {
    const trimmed = title.trim();
    document.title = trimmed ? `${trimmed} · ${DEFAULT_TITLE}` : DEFAULT_TITLE;

    return () => {
      document.title = DEFAULT_TITLE;
    };
  }, [title, pathname]);

  return null;
}
