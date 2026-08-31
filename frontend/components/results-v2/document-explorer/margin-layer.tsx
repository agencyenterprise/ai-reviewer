'use client';

import { Issue } from '@/lib/generated-api';
import { useLayoutEffect, useMemo, useRef, useState } from 'react';
import { DocumentIssues } from './document-issues';
import { MarginNote } from './margin-note';

/** Breathing room between two notes once one has been pushed under another. */
const GAP = 6;

type IssueWithLines = Issue & { start_line?: number | null };

interface MarginLayerProps {
  /** Issues anchored to a line, in the order they appear in the document. */
  issues: IssueWithLines[];
  /** Issues about the document rather than a place in it. */
  documentIssues: Issue[];
  activeIssueId: string | null;
  readOnly: boolean;
  onSelect: (issue: Issue) => void;
}

interface Entry {
  id: string;
  /** The line this note wants to sit beside, or null to ride at the top. */
  line: number | null;
  issue?: Issue;
  group?: Issue[];
}

/**
 * The notes, floating beside the document rather than inside it.
 *
 * They used to live in the third cell of each block's grid row, which made the
 * row as tall as its notes: a one-line paragraph carrying four issues opened a
 * hole in the text column the height of four cards. Word and Google Docs solve
 * this the same way, and so does this — the notes are taken out of the flow and
 * placed against the measured top of the paragraph they belong to, then pushed
 * down only as far as the note above them requires.
 *
 * Positions are measured rather than derived: line numbers say nothing about
 * height, and a paragraph's height depends on wrapping, images and maths that
 * only the browser knows.
 */
export function MarginLayer({ issues, documentIssues, activeIssueId, readOnly, onSelect }: MarginLayerProps) {
  const layerRef = useRef<HTMLDivElement>(null);
  const noteRefs = useRef(new Map<string, HTMLElement>());
  const [tops, setTops] = useState<Record<string, number>>({});

  const entries = useMemo<Entry[]>(() => {
    // Sorted by line, not by whatever order the list arrives in. The stack only
    // ever pushes a note *down*, so one out-of-place note near the top would
    // drag every note after it away from the paragraph it belongs to.
    const anchored = issues
      .map((issue) => ({
        id: issue.id,
        line: typeof issue.start_line === 'number' ? issue.start_line : null,
        issue: issue as Issue,
      }))
      .sort((a, b) => (a.line ?? 0) - (b.line ?? 0));
    // The document-level group rides at the top, above the first paragraph's
    // notes, because that is what it is about.
    return documentIssues.length > 0
      ? [{ id: '__document__', line: null, group: documentIssues }, ...anchored]
      : anchored;
  }, [issues, documentIssues]);

  useLayoutEffect(() => {
    const layer = layerRef.current;
    const body = layer?.parentElement;
    if (!layer || !body) return;

    const layout = () => {
      const bodyTop = body.getBoundingClientRect().top;
      const owners = Array.from(body.querySelectorAll<HTMLElement>('[data-block-owner]'));

      const next: Record<string, number> = {};
      let cursor = 0;

      for (const entry of entries) {
        const element = noteRefs.current.get(entry.id);
        const height = element?.offsetHeight ?? 0;

        // Where it would like to be: level with the top of its paragraph.
        let wanted = cursor;
        if (entry.line !== null) {
          const anchor = owners.find((owner) => {
            const start = Number(owner.dataset.lineStart);
            const end = Number(owner.dataset.lineEnd);
            return Number.isFinite(start) && Number.isFinite(end) && entry.line! >= start && entry.line! <= end;
          });
          if (anchor) wanted = anchor.getBoundingClientRect().top - bodyTop;
        }

        // Where it can be: never overlapping the note above it.
        const top = Math.max(wanted, cursor);
        next[entry.id] = top;
        cursor = top + height + GAP;
      }

      setTops((previous) => (sameTops(previous, next) ? previous : next));
    };

    layout();

    // The document reflows on resize, and a note changes height when it opens.
    const observer = new ResizeObserver(layout);
    observer.observe(body);
    noteRefs.current.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, [entries, activeIssueId]);

  if (entries.length === 0) return null;

  return (
    <div
      ref={layerRef}
      // Only the notes take clicks; the column itself must not cover the
      // document's own right edge.
      className="pointer-events-none absolute inset-y-0 right-0 hidden w-[calc(26rem_+_1px)] pl-4 xl:block"
    >
      {entries.map((entry) => (
        <div
          key={entry.id}
          ref={(element) => {
            if (element) noteRefs.current.set(entry.id, element);
            else noteRefs.current.delete(entry.id);
          }}
          style={{ top: tops[entry.id] ?? 0 }}
          className="pointer-events-auto absolute right-0 left-4 transition-[top] duration-150 ease-out"
        >
          {entry.group ? (
            <DocumentIssues
              issues={entry.group}
              activeIssueId={activeIssueId}
              readOnly={readOnly}
              onSelect={onSelect}
            />
          ) : (
            <MarginNote
              issue={entry.issue!}
              active={activeIssueId === entry.issue!.id}
              readOnly={readOnly}
              onSelect={onSelect}
            />
          )}
        </div>
      ))}
    </div>
  );
}

function sameTops(a: Record<string, number>, b: Record<string, number>): boolean {
  const keys = Object.keys(b);
  if (Object.keys(a).length !== keys.length) return false;
  return keys.every((key) => a[key] === b[key]);
}
