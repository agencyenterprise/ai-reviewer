import type { HandoffView } from '@/lib/generated-api';

/** A document with suggestions waiting, as the pane lists it when another one is open. */
export type WaitingDocument = { name: string; url: string; count: number };

/**
 * The handoffs waiting for other documents, one line per document: several requests
 * about one document (the same link asked about again and again) are one place to go.
 */
export function waitingDocuments(handoffs: HandoffView[]): WaitingDocument[] {
  const byUrl = new Map<string, WaitingDocument>();
  for (const handoff of handoffs) {
    const known = byUrl.get(handoff.document_url);
    if (known) known.count += 1;
    else
      byUrl.set(handoff.document_url, {
        name: handoff.document_name,
        url: openInBrowser(handoff.document_url),
        count: 1,
      });
  }
  return [...byUrl.values()];
}

/**
 * A document link that opens in Word for the web rather than downloading the file.
 *
 * Graph's `webUrl` for a file in a library is its plain path, which SharePoint serves as
 * a download; `web=1` asks it to open the file in the browser. A link that already goes
 * through a page (`…/_layouts/15/Doc.aspx?sourcedoc=…`) opens there as it is.
 */
export function openInBrowser(url: string): string {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return url;
  }
  if (parsed.pathname.toLowerCase().endsWith('.aspx') || parsed.searchParams.has('web')) return url;
  parsed.searchParams.set('web', '1');
  return parsed.toString();
}
