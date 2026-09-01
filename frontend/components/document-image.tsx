'use client';

import { ImageOff } from 'lucide-react';
import React from 'react';
import { defaultUrlTransform } from 'react-markdown';
import { useShare } from '@/context/share-context';

/**
 * Converted document markdown references extracted images by a
 * storage-agnostic `draftdetective://{file-id}` src (see the backend's
 * image_extraction service). Each consumer resolves the scheme to its own
 * retrieval mechanism; here that is the file-download endpoint, proxied by
 * the Next route of the same shape.
 */
const IMAGE_REFERENCE_SCHEME = 'draftdetective://';

/**
 * `urlTransform` for the document viewers' ReactMarkdown: resolves image
 * references to the download endpoint. Everything else gets react-markdown's
 * default sanitization, which would otherwise strip the unknown protocol
 * before `DocumentImage` could see it.
 */
export function documentUrlTransform(url: string): string {
  if (url.startsWith(IMAGE_REFERENCE_SCHEME)) {
    return `/api/files/download/${url.slice(IMAGE_REFERENCE_SCHEME.length)}`;
  }
  return defaultUrlTransform(url);
}

/**
 * Image renderer for converted document markdown, shared by the v1 and v2
 * document viewers.
 *
 * Documents converted before image extraction existed carry truncated
 * `data:image/png;base64...` stubs, which the url sanitization reduces to an
 * empty src; rendering those as <img> makes the browser refetch the page, so
 * they get an alt-text placeholder instead. In shared views the share token
 * is appended because an <img> request cannot carry the session's
 * Authorization header.
 */
export function DocumentImage({ src, alt, title }: React.ImgHTMLAttributes<HTMLImageElement>) {
  const { shareToken } = useShare();

  if (typeof src !== 'string' || src.length === 0 || src.startsWith('data:')) {
    return (
      <span className="my-1 inline-flex items-center gap-1.5 rounded border border-dashed px-2 py-1 text-xs text-muted-foreground">
        <ImageOff className="size-3" />
        {alt || 'Image not extracted'}
      </span>
    );
  }

  // Extraction carries the document's intended display size in the
  // reference's query parameters (`?w=&h=`) so the src stays a plain markdown
  // image — see the backend's image_reference. The size is read here and kept
  // out of the request.
  const [path, query] = src.split('?');
  const params = new URLSearchParams(query);
  const width = params.get('w') ?? undefined;
  const height = params.get('h') ?? undefined;
  params.delete('w');
  params.delete('h');
  if (shareToken && path.startsWith('/api/')) {
    params.set('share_token', shareToken);
  }
  const remaining = params.toString();
  const resolvedSrc = remaining ? `${path}?${remaining}` : path;

  // Without a declared size, cap the height so a print-resolution image
  // doesn't dwarf the viewer. `h-auto max-w-full` keeps the ratio when the
  // pane is narrower than the declared width.
  const sizeClass = width || height ? 'h-auto' : 'max-h-[32rem]';

  // No loading="lazy": Chrome defers lazy images inside this overflow scroll
  // container far too aggressively (deep links land on blank blocks), and a
  // document carries few images anyway.
  return (
    // eslint-disable-next-line @next/next/no-img-element -- document content, not app chrome
    <img
      src={resolvedSrc}
      alt={alt ?? ''}
      width={width}
      height={height}
      title={title}
      className={`my-2 max-w-full rounded ${sizeClass}`}
    />
  );
}
