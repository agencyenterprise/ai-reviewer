'use client';

import DOMPurify from 'dompurify';
import { Ref, useImperativeHandle, useMemo, useRef } from 'react';

// The report HTML is authored by an LLM and is untrusted. It is rendered inside
// a sandboxed iframe (no allow-scripts, no allow-same-origin) so nothing in it
// can execute or reach the app, plus an injected CSP that blocks any external
// resource load, plus DOMPurify as defense in depth.
const REPORT_CSP = "default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:;";

function injectCspMeta(doc: string): string {
  const meta = `<meta http-equiv="Content-Security-Policy" content="${REPORT_CSP}">`;
  if (/<head[^>]*>/i.test(doc)) return doc.replace(/<head[^>]*>/i, (m) => `${m}${meta}`);
  if (/<html[^>]*>/i.test(doc)) return doc.replace(/<html[^>]*>/i, (m) => `${m}<head>${meta}</head>`);
  return `<!doctype html><html><head>${meta}</head><body>${doc}</body></html>`;
}

function buildSrcDoc(html: string): string {
  // DOMPurify needs a DOM; skip on the server (the iframe renders client-side).
  if (typeof window === 'undefined') return '';
  const clean = DOMPurify.sanitize(html, {
    WHOLE_DOCUMENT: true,
    FORBID_TAGS: ['script'],
    ADD_ATTR: ['target'],
  });
  return injectCspMeta(clean);
}

export interface HtmlReportFrameHandle {
  /** Open the browser print dialog scoped to the report (Save as PDF). */
  print: () => void;
}

interface HtmlReportFrameProps {
  html: string;
  title?: string;
  className?: string;
  ref?: Ref<HtmlReportFrameHandle>;
}

export function HtmlReportFrame({ html, title = 'Report', className, ref }: HtmlReportFrameProps) {
  const srcDoc = useMemo(() => buildSrcDoc(html), [html]);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useImperativeHandle(ref, () => ({
    print: () => {
      const win = iframeRef.current?.contentWindow;
      if (!win) return;
      win.focus();
      win.print();
    },
  }));

  return (
    <iframe
      ref={iframeRef}
      title={title}
      // No allow-scripts: nothing in the (untrusted, LLM-authored) document can
      // execute — enforced alongside the injected CSP and DOMPurify. allow-same-origin
      // lets the app invoke print() on the frame; allow-modals lets the print
      // dialog open. Neither enables script execution without allow-scripts.
      sandbox="allow-same-origin allow-modals"
      srcDoc={srcDoc}
      className={className ?? 'w-full h-[75vh] rounded-lg border bg-white'}
    />
  );
}
