'use client';

import { Issue, SeverityEnum } from '@/lib/generated-api';
import { isIssueResolved } from '@/lib/stores/document-explorer-store';
import { cn } from '@/lib/utils';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Ref, useImperativeHandle, useMemo } from 'react';
import { SEVERITY } from '@/lib/severity-style';
import { IssueBody, IssueMeta, IssuePreview } from './issue-note';

/** Worst first, matching the order the store already sorts issues into. */
const SEVERITY_ORDER: SeverityEnum[] = [SeverityEnum.High, SeverityEnum.Medium, SeverityEnum.Low, SeverityEnum.None];

type Row = { kind: 'header'; severity: SeverityEnum; count: number } | { kind: 'issue'; issue: Issue };

export interface IssuesListHandle {
  scrollToIssue: (issue: Issue) => void;
}

interface IssuesListProps {
  ref?: Ref<IssuesListHandle>;
  issues: Issue[];
  scrollElement: HTMLElement | null;
  activeIssueId: string | null;
  readOnly: boolean;
  onSelect: (issue: Issue) => void;
}

/**
 * The issue queue: grouped by severity, one flat row per issue, expanding in
 * place into the same body the margin note shows. Virtualised, because turning
 * passing checks on can push this past six hundred rows.
 */
export function IssuesList({ ref, issues, scrollElement, activeIssueId, readOnly, onSelect }: IssuesListProps) {
  const rows = useMemo<Row[]>(() => {
    const out: Row[] = [];
    for (const severity of SEVERITY_ORDER) {
      const group = issues.filter((issue) => issue.severity === severity);
      if (group.length === 0) continue;
      out.push({ kind: 'header', severity, count: group.length });
      for (const issue of group) out.push({ kind: 'issue', issue });
    }
    return out;
  }, [issues]);

  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => scrollElement,
    estimateSize: (index) => (rows[index].kind === 'header' ? 33 : 56),
    overscan: 8,
    getItemKey: (index) => {
      const row = rows[index];
      return row.kind === 'header' ? `header-${row.severity}` : row.issue.id;
    },
  });

  // Expanding a row in place should not yank the scroll position around it.
  virtualizer.shouldAdjustScrollPositionOnItemSizeChange = () => false;

  useImperativeHandle(
    ref,
    () => ({
      scrollToIssue: (issue: Issue) => {
        const index = rows.findIndex((row) => row.kind === 'issue' && row.issue.id === issue.id);
        if (index >= 0) virtualizer.scrollToIndex(index, { align: 'start' });
      },
    }),
    [rows, virtualizer],
  );

  return (
    <div style={{ height: virtualizer.getTotalSize(), position: 'relative', width: '100%' }}>
      {virtualizer.getVirtualItems().map((virtualItem) => {
        const row = rows[virtualItem.index];
        return (
          <div
            key={virtualItem.key}
            data-index={virtualItem.index}
            ref={virtualizer.measureElement}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {row.kind === 'header' ? (
              <GroupHeader severity={row.severity} count={row.count} />
            ) : (
              <IssueRow
                issue={row.issue}
                active={activeIssueId === row.issue.id}
                readOnly={readOnly}
                onSelect={onSelect}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function GroupHeader({ severity, count }: { severity: SeverityEnum; count: number }) {
  const style = SEVERITY[severity];
  return (
    <div className="bg-background flex items-center gap-2 border-b px-4 py-2">
      <span className={cn('block size-2 rounded-[2px]', style.dot)} />
      <span className="text-xs font-medium">{style.label}</span>
      <span className="font-mono text-[11px] tabular-nums text-muted-foreground">{count}</span>
    </div>
  );
}

function IssueRow({
  issue,
  active,
  readOnly,
  onSelect,
}: {
  issue: Issue;
  active: boolean;
  readOnly: boolean;
  onSelect: (issue: Issue) => void;
}) {
  const resolved = isIssueResolved(issue);
  const style = SEVERITY[issue.severity];

  return (
    <div
      onClick={() => onSelect(issue)}
      role="button"
      tabIndex={0}
      aria-expanded={active}
      onKeyDown={(event) => {
        // Only when the row itself has focus: an expanded row holds Resolve and
        // feedback buttons, and swallowing their Enter would collapse the row
        // rather than press them.
        if (event.target !== event.currentTarget) return;
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onSelect(issue);
        }
      }}
      className={cn(
        'w-full cursor-pointer border-b px-4 py-3 text-left transition-colors',
        active ? style.wash : 'hover:bg-accent/50',
        resolved && !active && 'opacity-60',
      )}
    >
      <IssueMeta issue={issue} />
      <span className="mt-1 flex items-start gap-2">
        <span className="flex-1 text-[13.5px] leading-snug font-medium">{issue.title}</span>
        {active && <span className={cn('shrink-0 font-mono text-[10px] uppercase', style.text)}>{style.label}</span>}
      </span>
      {!active && <IssuePreview issue={issue} />}
      {active && (
        <div className="mt-2">
          <IssueBody issue={issue} readOnly={readOnly} />
        </div>
      )}
    </div>
  );
}
