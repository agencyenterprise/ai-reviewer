'use client';

import type { Issue } from '@/lib/generated-api';
import { SeverityEnum } from '@/lib/generated-api';
import { cn } from '@/lib/utils';
import type { Element } from 'hast';
import { ImageOff } from 'lucide-react';
import { SEVERITY } from '@/lib/severity-style';
import { DocumentIssues } from './document-issues';
import { MarginNote } from './margin-note';
import React, { Ref, createContext, useContext, useEffect, useImperativeHandle, useMemo, useRef } from 'react';
import ReactMarkdown, { type ExtraProps } from 'react-markdown';
import rehypeMathML from '@daiji256/rehype-mathml';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import type { PluggableList } from 'unified';

interface IssueWithLines extends Issue {
  start_line?: number | null;
  end_line?: number | null;
}

export interface DocumentViewHandle {
  scrollToLineRange: (range: [number, number]) => void;
  scrollToLine: (line: number, behavior?: ScrollBehavior) => void;
  /** Source line of the block currently at the top of the pane. */
  getTopVisibleLine: () => number | null;
}

interface DocumentViewProps {
  ref?: Ref<DocumentViewHandle>;
  markdown: string;
  issues: Issue[];
  selectedLineRange: [number, number] | null;
  onIssueSelect: (issue: Issue | null) => void;
  /**
   * When set, issues are rendered in a margin column beside the paragraph they
   * belong to, sharing this pane's scroll. Omit for a plain document.
   */
  margin?: { activeIssueId: string | null; readOnly: boolean; onSelect: (issue: Issue) => void };
}

const SEVERITY_RANK: Record<string, number> = {
  [SeverityEnum.None]: 0,
  [SeverityEnum.Low]: 1,
  [SeverityEnum.Medium]: 2,
  [SeverityEnum.High]: 3,
};

/** Resting mark on flagged text, as in the mock: the mark is on the text, not behind it. */
const FLAGGED_CLASSES = ['underline', 'decoration-dotted', 'underline-offset-4', 'decoration-muted-foreground/50'];

const CLEARED_CLASSES = [
  ...new Set(Object.values(SEVERITY).flatMap((style) => style.wash.split(' '))),
  ...FLAGGED_CLASSES,
  'cursor-pointer',
];

function hasLineRange(issue: Issue): issue is IssueWithLines & { start_line: number; end_line: number } {
  const start = (issue as IssueWithLines).start_line;
  const end = (issue as IssueWithLines).end_line;
  return typeof start === 'number' && typeof end === 'number';
}

function pickTopSeverityIssue(issues: IssueWithLines[], lineStart: number, lineEnd: number) {
  let best: IssueWithLines | null = null;
  for (const issue of issues) {
    if (!hasLineRange(issue)) continue;
    const overlaps = issue.start_line! <= lineEnd && issue.end_line! >= lineStart;
    if (!overlaps) continue;
    if (!best || SEVERITY_RANK[issue.severity] > SEVERITY_RANK[best.severity]) {
      best = issue;
    }
  }
  return best;
}

function rangesOverlap(a: [number, number], b: [number, number]): boolean {
  return a[0] <= b[1] && a[1] >= b[0];
}

const SCROLL_RETRY_MS = 50;
const SCROLL_MAX_ATTEMPTS = 20;

/** First rendered block whose source lines overlap `range`, or null while none is laid out. */
function findBlockForRange(container: HTMLElement, range: [number, number]): HTMLElement | null {
  const blocks = container.querySelectorAll<HTMLElement>('[data-line-start][data-line-end]');
  for (const block of blocks) {
    const start = Number(block.getAttribute('data-line-start'));
    const end = Number(block.getAttribute('data-line-end'));
    if (Number.isFinite(start) && Number.isFinite(end) && rangesOverlap([start, end], range)) {
      return block;
    }
  }
  return null;
}

/**
 * Both modes must give the text column the same width, or switching between them
 * rewraps the document and the reader's place in it moves.
 *
 * The trick is to keep the non-text overhead identical: in margin mode that is
 * the gutter plus the margin column, and in list mode it is the gutter plus the
 * issues aside, which sits outside this pane. The extra pixel matches the
 * aside's left border. Below `xl` the margin column is not rendered and the
 * aside takes over, so two columns are the base and the third arrives at `xl`.
 *
 * Written out in full because Tailwind reads class names as literal strings.
 */
const GRID_BASE = 'grid-cols-[3rem_minmax(0,46rem)]';
const GRID_WITH_MARGIN = 'xl:grid-cols-[3rem_minmax(0,46rem)_calc(26rem_+_1px)]';
const WIDTH_BASE = 'max-w-[calc(3rem_+_46rem)]';
const WIDTH_WITH_MARGIN = 'xl:max-w-[calc(3rem_+_46rem_+_26rem_+_1px)]';

/**
 * True inside a container block (list, quote, table). Nested blocks skip the
 * gutter so only top-level blocks are numbered, the way an editor numbers lines.
 */
const NestedContext = createContext(false);

interface MarginState {
  issues: IssueWithLines[];
  activeIssueId: string | null;
  readOnly: boolean;
  onSelect: (issue: Issue) => void;
}

const MarginContext = createContext<MarginState | null>(null);

/**
 * Notes for one row: the issues that *begin* inside it. An issue can span several
 * blocks, so anchoring on its first line keeps each note in exactly one place —
 * and keeps this pure, which claiming into a shared set was not: React invokes a
 * component's render more than once, and the second pass would find its own
 * issues already taken.
 */
function useRowNotes(lineStart: number | undefined, lineEnd: number | undefined) {
  const margin = useContext(MarginContext);
  if (!margin || lineStart === undefined || lineEnd === undefined) return null;

  const notes = margin.issues.filter((issue) => issue.start_line! >= lineStart && issue.start_line! <= lineEnd);

  return { notes, margin };
}

/**
 * `spacing` goes on the row rather than the element so the line number stays on
 * the first line of its block — a heading's top margin has to move both columns
 * or the number drifts above the text it belongs to.
 */
function blockFactory(Tag: string, spacing: string, className: string, isContainer = false, scrollWrap = false) {
  function Block({ node, children, ...rest }: React.HTMLAttributes<HTMLElement> & ExtraProps) {
    const nested = useContext(NestedContext);
    const position = (node as Element | undefined)?.position;
    const lineStart = position?.start.line;
    const lineEnd = position?.end.line;

    const dataProps: Record<string, string | number> = {};
    if (lineStart !== undefined) dataProps['data-line-start'] = lineStart;
    if (lineEnd !== undefined) dataProps['data-line-end'] = lineEnd;

    const isRow = !nested && lineStart !== undefined;
    const body = isContainer ? <NestedContext.Provider value>{children}</NestedContext.Provider> : children;
    const element = React.createElement(
      Tag,
      {
        ...rest,
        ...dataProps,
        // The shared classes come first so a block's own padding wins: tailwind-merge
        // drops the earlier of two conflicting utilities, which was silently
        // removing the lists' indent and leaving their markers over the gutter.
        className: cn('-mx-2 rounded-sm px-2 transition-colors', className, !isRow && spacing, rest.className),
      },
      body,
    );

    const content = scrollWrap ? <div className="max-w-full overflow-x-auto">{element}</div> : element;
    const row = useRowNotes(isRow ? lineStart : undefined, isRow ? lineEnd : undefined);

    if (!isRow) return content;

    return (
      <div data-block-row className={cn('grid', spacing, GRID_BASE, row && GRID_WITH_MARGIN)}>
        {/* The rule sits beside the text rather than in the gutter cell so it
            measures the paragraph, not the row — a row can be tall because its
            margin holds several notes. */}
        <div className="justify-end pt-[0.15em] pr-2 text-right select-none" aria-hidden>
          <span className="font-mono text-[10.5px] leading-[1.7] tabular-nums text-muted-foreground/60">
            {lineStart}
          </span>
        </div>
        <div className="flex min-w-0 gap-2 self-start">
          <span data-rule className="w-[2px] shrink-0 rounded-full bg-transparent" />
          <div className="min-w-0 flex-1">{content}</div>
        </div>
        {row && (
          <div className="col-start-3 hidden self-start pl-4 xl:block">
            {row.notes.map((issue) => (
              <MarginNote
                key={issue.id}
                issue={issue}
                active={row.margin.activeIssueId === issue.id}
                readOnly={row.margin.readOnly}
                onSelect={row.margin.onSelect}
              />
            ))}
          </div>
        )}
      </div>
    );
  }
  Block.displayName = `DocumentBlock-${Tag}`;
  return Block;
}

const REMARK_PLUGINS: PluggableList = [remarkGfm, [remarkMath, { singleDollarTextMath: false }]];
const REHYPE_PLUGINS: PluggableList = [rehypeMathML, [rehypeRaw, { tagfilter: true }]];

const BLOCK_COMPONENTS = {
  p: blockFactory('p', 'mb-3', 'leading-[1.7]'),
  h1: blockFactory('h1', 'mt-6 mb-3', 'text-xl font-semibold tracking-tight'),
  h2: blockFactory('h2', 'mt-7 mb-2', 'text-lg font-semibold tracking-tight'),
  h3: blockFactory('h3', 'mt-5 mb-2', 'text-base font-semibold'),
  h4: blockFactory('h4', 'mt-4 mb-2', 'text-base font-semibold'),
  h5: blockFactory('h5', 'mt-4 mb-2', 'text-base font-medium'),
  h6: blockFactory('h6', 'mt-4 mb-2', 'text-base font-medium'),
  ul: blockFactory('ul', 'mb-3', 'list-disc pl-8', true),
  ol: blockFactory('ol', 'mb-3', 'list-decimal pl-8', true),
  li: blockFactory('li', 'mb-1', 'leading-[1.7]'),
  blockquote: blockFactory('blockquote', 'mb-3', 'border-l-2 border-border pl-4 text-muted-foreground', true),
  pre: blockFactory('pre', 'mb-3', 'max-w-full overflow-x-auto rounded bg-muted px-2 py-1'),
  table: blockFactory('table', 'mb-3', 'w-full border-collapse text-left text-[13px]', true, true),
  thead: ({ children }: React.HTMLAttributes<HTMLElement>) => <thead className="border-b">{children}</thead>,
  th: ({ children }: React.HTMLAttributes<HTMLElement>) => (
    <th className="px-2 py-1.5 font-medium whitespace-nowrap">{children}</th>
  ),
  td: ({ children }: React.HTMLAttributes<HTMLElement>) => (
    <td className="border-t px-2 py-1.5 align-top">{children}</td>
  ),
  hr: blockFactory('hr', 'my-5', ''),
  // DOCX extraction leaves images with no src behind; rendering them as <img>
  // makes the browser refetch the page, so show the alt text instead.
  img: ({ src, alt }: React.ImgHTMLAttributes<HTMLImageElement>) =>
    typeof src === 'string' && src.length > 0 ? (
      // eslint-disable-next-line @next/next/no-img-element -- document content, not app chrome
      <img src={src} alt={alt ?? ''} className="my-2 max-w-full rounded" />
    ) : (
      <span className="my-1 inline-flex items-center gap-1.5 rounded border border-dashed px-2 py-1 text-xs text-muted-foreground">
        <ImageOff className="size-3" />
        {alt || 'Image not extracted'}
      </span>
    ),
};

export function DocumentView({ ref, markdown, issues, selectedLineRange, onIssueSelect, margin }: DocumentViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  /**
   * Retried on a timer rather than via requestAnimationFrame: rAF never fires while
   * the tab is hidden, and the document can still be laying out when a line jump
   * arrives from another tab's route. Scrolls the container itself rather than
   * block.scrollIntoView(), which would also scroll ancestors.
   */
  const scrollToRange = (range: [number, number], align: 'center' | 'start', behavior: ScrollBehavior = 'smooth') => {
    let attempts = 0;
    const attempt = () => {
      const container = containerRef.current;
      if (!container) return;

      const block = findBlockForRange(container, range);
      if (!block || container.clientHeight === 0) {
        if (attempts++ < SCROLL_MAX_ATTEMPTS) setTimeout(attempt, SCROLL_RETRY_MS);
        return;
      }

      // `container` is positioned, so offsetTop is already relative to it.
      const top =
        align === 'center'
          ? block.offsetTop - container.clientHeight / 2 + block.offsetHeight / 2
          : block.offsetTop - 12;
      container.scrollTo({ top: Math.max(0, top), behavior });
    };
    attempt();
  };

  useImperativeHandle(ref, () => ({
    scrollToLineRange: (range: [number, number]) => scrollToRange(range, 'center'),
    scrollToLine: (line: number, behavior: ScrollBehavior = 'smooth') => scrollToRange([line, line], 'start', behavior),
    getTopVisibleLine: () => {
      const container = containerRef.current;
      if (!container) return null;
      const blocks = container.querySelectorAll<HTMLElement>('[data-line-start]');
      for (const block of blocks) {
        if (block.offsetTop + block.offsetHeight > container.scrollTop) {
          const line = Number(block.getAttribute('data-line-start'));
          return Number.isFinite(line) ? line : null;
        }
      }
      return null;
    },
  }));

  const lineIssues = useMemo(() => issues.filter(hasLineRange) as IssueWithLines[], [issues]);
  // The rest: findings about the document rather than a place in it, like a
  // missing Abbreviations section. Nothing anchors them, so the margin would
  // drop them entirely and the header would count issues that are not on screen.
  const documentIssues = useMemo(() => issues.filter((issue) => !hasLineRange(issue)), [issues]);

  // The parsed tree only depends on the markdown; highlights and click handlers
  // are applied imperatively below so a filter change never reparses.
  const renderedMarkdown = useMemo(
    () => (
      <ReactMarkdown remarkPlugins={REMARK_PLUGINS} rehypePlugins={REHYPE_PLUGINS} components={BLOCK_COMPONENTS}>
        {markdown}
      </ReactMarkdown>
    ),
    [markdown],
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const blocks = container.querySelectorAll<HTMLElement>('[data-line-start][data-line-end]');
    const cleanups: Array<() => void> = [];

    blocks.forEach((block) => {
      const lineStart = Number(block.getAttribute('data-line-start'));
      const lineEnd = Number(block.getAttribute('data-line-end'));
      if (!Number.isFinite(lineStart) || !Number.isFinite(lineEnd)) return;

      const rule = block.closest('[data-block-row]')?.querySelector<HTMLElement>('[data-rule]');

      block.classList.remove(...CLEARED_CLASSES);
      block.removeAttribute('data-issue-id');
      block.removeAttribute('data-issue-selected');
      if (rule) {
        rule.className = 'w-[2px] shrink-0 rounded-full bg-transparent';
      }

      const issue = pickTopSeverityIssue(lineIssues, lineStart, lineEnd);
      if (!issue) return;

      // Selected means this block is inside the selected lines — not merely that
      // it carries an issue overlapping them. Otherwise a heading whose own issue
      // spans into the selection lights up alongside the paragraph you picked.
      const isSelected = selectedLineRange !== null && rangesOverlap([lineStart, lineEnd], selectedLineRange);

      block.classList.add('cursor-pointer', ...FLAGGED_CLASSES);
      block.setAttribute('data-issue-id', issue.id);
      block.setAttribute('data-issue-selected', String(isSelected));

      if (isSelected) {
        block.classList.add(...SEVERITY[issue.severity].wash.split(' '));
      }

      if (rule) {
        rule.className = cn('w-[2px] shrink-0 rounded-full', SEVERITY[issue.severity].dot);
      }

      const handler = (event: Event) => {
        event.stopPropagation();
        onIssueSelect(isSelected ? null : issue);
      };
      block.addEventListener('click', handler);
      cleanups.push(() => block.removeEventListener('click', handler));
    });

    return () => {
      for (const cleanup of cleanups) cleanup();
    };
  }, [markdown, lineIssues, selectedLineRange, onIssueSelect]);

  const marginState: MarginState | null = margin ? { issues: lineIssues, ...margin } : null;

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative h-full overflow-x-hidden overflow-y-auto px-5 py-5 text-sm break-words',
        // MathML does not wrap, so give it its own scroll rather than letting it
        // run past the text column.
        '[&_math]:inline-block [&_math]:max-w-full [&_math]:overflow-x-auto [&_math]:align-middle',
      )}
    >
      <MarginContext.Provider value={marginState}>
        <div className={cn('mx-auto', WIDTH_BASE, marginState && WIDTH_WITH_MARGIN)}>
          {marginState && documentIssues.length > 0 && (
            <div className={cn('grid', GRID_BASE, GRID_WITH_MARGIN)}>
              {/* Empty gutter and text cells: these notes sit above the document
                  rather than beside any part of it. */}
              <div aria-hidden />
              <div aria-hidden />
              <div className="col-start-3 hidden self-start pb-4 pl-4 xl:block">
                <DocumentIssues
                  issues={documentIssues}
                  activeIssueId={marginState.activeIssueId}
                  readOnly={marginState.readOnly}
                  onSelect={marginState.onSelect}
                />
              </div>
            </div>
          )}
          {renderedMarkdown}
        </div>
      </MarginContext.Provider>
    </div>
  );
}
