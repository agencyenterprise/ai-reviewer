'use client';

/**
 * Names the browser tab after what is on screen.
 *
 * A rendered `<title>` rather than route metadata: these pages are client
 * components whose subject arrives from a query, which `generateMetadata` on
 * the server has no way to read. React hoists this into the head, and the last
 * one rendered wins over the app-wide default.
 */
export function PageTitle({ title }: { title: string }) {
  const trimmed = title.trim();

  return <title>{trimmed ? `${trimmed} · Draft Detective` : 'Draft Detective'}</title>;
}
