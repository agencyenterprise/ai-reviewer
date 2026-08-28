'use client';

import type { Issue } from '@/lib/generated-api';
import { SeverityEnum } from '@/lib/generated-api';
import { cn } from '@/lib/utils';
import type { Element } from 'hast';
import { ImageOff } from 'lucide-react';
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
  scrollToLine: (line: number) => void;
}

interface DocumentViewProps {
  ref?: Ref<DocumentViewHandle>;
  markdown: string;
  issues: Issue[];
  selectedLineRange: [number, number] | null;
  onIssueSelect: (issue: Issue | null) => void;
  /** Optional content rendered inside the scroll area, above the document. */
  header?: React.ReactNode;
}

/** Gutter rule colour, one per severity. Same families the issue cards use. */
const SEVERITY_RULE: Record<string, string> = {
  [SeverityEnum.High]: 'bg-red-500',
  [SeverityEnum.Medium]: 'bg-amber-500',
  [SeverityEnum.Low]: 'bg-blue-500',
  [SeverityEnum.None]: 'bg-green-500',
};

/** Resting wash on a flagged block — quiet enough to read through. */
const SEVERITY_WASH: Record<string, string> = {
  [SeverityEnum.High]: 'bg-red-50/70 dark:bg-red-950/20',
  [SeverityEnum.Medium]: 'bg-amber-50/70 dark:bg-amber-950/20',
  [SeverityEnum.Low]: 'bg-blue-50/70 dark:bg-blue-950/20',
  [SeverityEnum.None]: 'bg-green-50/70 dark:bg-green-950/20',
};

/** Wash once the block is the selected one. */
const SEVERITY_WASH_SELECTED: Record<string, string> = {
  [SeverityEnum.High]: 'bg-red-100 dark:bg-red-950/50',
  [SeverityEnum.Medium]: 'bg-amber-100 dark:bg-amber-950/50',
  [SeverityEnum.Low]: 'bg-blue-100 dark:bg-blue-950/50',
  [SeverityEnum.None]: 'bg-green-100 dark:bg-green-950/50',
};

const SEVERITY_RANK: Record<string, number> = {
  [SeverityEnum.None]: 0,
  [SeverityEnum.Low]: 1,
  [SeverityEnum.Medium]: 2,
  [SeverityEnum.High]: 3,
};

const CLEARED_CLASSES = [
  ...new Set(
    [...Object.values(SEVERITY_WASH), ...Object.values(SEVERITY_WASH_SELECTED)].flatMap((cls) => cls.split(' ')),
  ),
  'cursor-pointer',
  'opacity-50',
  'ring-1',
  'ring-inset',
  'ring-foreground/15',
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
 * True inside a container block (list, quote, table). Nested blocks skip the
 * gutter so only top-level blocks are numbered, the way an editor numbers lines.
 */
const NestedContext = createContext(false);

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
        className: cn(className, '-mx-2 rounded-sm px-2 transition-colors', !isRow && spacing, rest.className),
      },
      body,
    );

    const content = scrollWrap ? <div className="max-w-full overflow-x-auto">{element}</div> : element;

    if (!isRow) return content;

    return (
      <div data-block-row className={cn('grid grid-cols-[3rem_minmax(0,1fr)] gap-x-2', spacing)}>
        <div className="flex justify-end gap-2 select-none" aria-hidden>
          <span className="pt-[0.15em] font-mono text-[10.5px] leading-[1.7] tabular-nums text-muted-foreground/60">
            {lineStart}
          </span>
          <span data-rule className="w-[2px] shrink-0 rounded-full bg-transparent" />
        </div>
        <div className="min-w-0">{content}</div>
      </div>
    );
  }
  Block.displayName = `DocumentBlock-${Tag}`;
  return Block;
}

const REMARK_PLUGINS: PluggableList = [remarkGfm, remarkMath];
const REHYPE_PLUGINS: PluggableList = [rehypeMathML, [rehypeRaw, { tagfilter: true }]];

const BLOCK_COMPONENTS = {
  p: blockFactory('p', 'mb-3', 'leading-[1.7]'),
  h1: blockFactory('h1', 'mt-6 mb-3', 'text-xl font-semibold tracking-tight'),
  h2: blockFactory('h2', 'mt-7 mb-2', 'text-lg font-semibold tracking-tight'),
  h3: blockFactory('h3', 'mt-5 mb-2', 'text-base font-semibold'),
  h4: blockFactory('h4', 'mt-4 mb-2', 'text-base font-semibold'),
  h5: blockFactory('h5', 'mt-4 mb-2', 'text-base font-medium'),
  h6: blockFactory('h6', 'mt-4 mb-2', 'text-base font-medium'),
  ul: blockFactory('ul', 'mb-3', 'ml-6 list-disc', true),
  ol: blockFactory('ol', 'mb-3', 'ml-6 list-decimal', true),
  li: blockFactory('li', 'mb-1', ''),
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

export function DocumentView({ ref, markdown, issues, selectedLineRange, onIssueSelect, header }: DocumentViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  /**
   * Retried on a timer rather than via requestAnimationFrame: rAF never fires while
   * the tab is hidden, and the document can still be laying out when a line jump
   * arrives from another tab's route. Scrolls the container itself rather than
   * block.scrollIntoView(), which would also scroll ancestors.
   */
  const scrollToRange = (range: [number, number], align: 'center' | 'start') => {
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
      container.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
    };
    attempt();
  };

  useImperativeHandle(ref, () => ({
    scrollToLineRange: (range: [number, number]) => scrollToRange(range, 'center'),
    scrollToLine: (line: number) => scrollToRange([line, line], 'start'),
  }));

  const lineIssues = useMemo(() => issues.filter(hasLineRange) as IssueWithLines[], [issues]);

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

      const issueRange: [number, number] = [issue.start_line!, issue.end_line!];
      const isSelected = selectedLineRange !== null && rangesOverlap(issueRange, selectedLineRange);

      const wash = isSelected ? SEVERITY_WASH_SELECTED[issue.severity] : SEVERITY_WASH[issue.severity];
      if (wash) block.classList.add(...wash.split(' '));
      block.classList.add('cursor-pointer');
      block.setAttribute('data-issue-id', issue.id);

      if (rule) {
        rule.className = cn('w-[2px] shrink-0 rounded-full', SEVERITY_RULE[issue.severity]);
      }

      if (selectedLineRange) {
        block.setAttribute('data-issue-selected', String(isSelected));
        if (isSelected) {
          block.classList.add('ring-1', 'ring-inset', 'ring-foreground/15');
        } else {
          block.classList.add('opacity-50');
          if (rule) rule.classList.add('opacity-50');
        }
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

  return (
    <div ref={containerRef} className="relative h-full overflow-x-hidden overflow-y-auto px-5 py-5 text-sm break-words">
      {header && <div className="mb-4">{header}</div>}
      <div className="mx-auto max-w-[78ch]">{renderedMarkdown}</div>
    </div>
  );
}
