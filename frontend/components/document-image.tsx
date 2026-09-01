'use client';

import { ImageOff } from 'lucide-react';
import React from 'react';
import { useShare } from '@/context/share-context';

/**
 * Image renderer for converted document markdown, shared by the v1 and v2
 * document viewers.
 *
 * Documents converted before image extraction existed carry truncated
 * `data:image/png;base64...` stubs — no comma, no payload — and rendering
 * those as <img> makes the browser issue a garbage request, so they get an
 * alt-text placeholder instead. Extracted images have relative
 * `/api/files/{file_id}/images/{index}` srcs served by the Next proxy route
 * of the same shape; in shared views the share token is appended because an
 * <img> request cannot carry the session's Authorization header.
 */
export function DocumentImage({ src, alt }: React.ImgHTMLAttributes<HTMLImageElement>) {
  const { shareToken } = useShare();

  const isBrokenDataUri = typeof src === 'string' && src.startsWith('data:') && !src.includes(',');
  if (typeof src !== 'string' || src.length === 0 || isBrokenDataUri) {
    return (
      <span className="my-1 inline-flex items-center gap-1.5 rounded border border-dashed px-2 py-1 text-xs text-muted-foreground">
        <ImageOff className="size-3" />
        {alt || 'Image not extracted'}
      </span>
    );
  }

  const resolvedSrc =
    shareToken && src.startsWith('/api/') ? `${src}?share_token=${encodeURIComponent(shareToken)}` : src;

  return (
    // eslint-disable-next-line @next/next/no-img-element -- document content, not app chrome
    <img src={resolvedSrc} alt={alt ?? ''} loading="lazy" className="my-2 max-h-[32rem] max-w-full rounded" />
  );
}
