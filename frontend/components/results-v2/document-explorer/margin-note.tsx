'use client';

import { Issue, SeverityEnum } from '@/lib/generated-api';
import { isIssueResolved } from '@/lib/stores/document-explorer-store';
import { cn } from '@/lib/utils';
import { IssueBody, IssueMeta, SEVERITY } from './issue-note';

interface MarginNoteProps {
  issue: Issue;
  active: boolean;
  readOnly: boolean;
  onSelect: (issue: Issue) => void;
}

/**
 * One issue in the document's margin, on the same grid row as the paragraph it
 * belongs to. Collapsed it is two lines, so a document with a hundred issues
 * stays readable; open it carries everything the issue list does.
 */
export function MarginNote({ issue, active, readOnly, onSelect }: MarginNoteProps) {
  const resolved = isIssueResolved(issue);
  const style = SEVERITY[issue.severity];

  return (
    <div className="relative mb-1">
      {/* The open note floats over the ones below rather than growing the row:
          expanding in place would shift the paragraph you are reading. */}
      {active && (
        <div className="bg-background absolute top-0 left-0 z-20 w-full rounded-md shadow-lg">
          <Leader severity={issue.severity} />
          <div className={cn('rounded-md border', style.edge, style.wash)}>
            <button
              onClick={() => onSelect(issue)}
              className="w-full cursor-pointer px-2.5 pt-2 text-left"
              aria-label="Collapse issue"
            >
              <IssueMeta issue={issue} />
              <span className="mt-0.5 flex items-start gap-2">
                <span className="flex-1 text-[13px] leading-snug font-medium">{issue.title}</span>
                <span className={cn('shrink-0 font-mono text-[10px] uppercase', style.text)}>{style.label}</span>
              </span>
            </button>
            <div className="px-2.5 pt-1.5 pb-2">
              <IssueBody issue={issue} readOnly={readOnly} />
            </div>
          </div>
        </div>
      )}

      <button
        onClick={() => onSelect(issue)}
        aria-expanded={active}
        className={cn(
          'hover:bg-accent/60 w-full cursor-pointer rounded-md px-2 py-1.5 text-left transition-colors',
          resolved && 'opacity-60',
          active && 'invisible',
        )}
      >
        <IssueMeta issue={issue} />
        <span className="mt-0.5 block text-[13px] leading-snug font-medium">{issue.title}</span>
      </button>
    </div>
  );
}

/** Hairline from the text column into the margin, tying a note to its paragraph. */
function Leader({ severity }: { severity: SeverityEnum }) {
  return <span aria-hidden className={cn('absolute top-3.5 -left-6 h-px w-6 opacity-60', SEVERITY[severity].dot)} />;
}
