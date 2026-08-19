'use client';

import { DocumentIssueCard } from '@/components/results/components/document-issue-card';
import { Card, CardContent } from '@/components/ui/card';
import { SeverityFilter } from '@/components/results/components/severity-filter';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Issue, SeverityEnum } from '@/lib/generated-api';
import { cn } from '@/lib/utils';
import { CheckCircle2, ChevronDownIcon } from 'lucide-react';
import { useState } from 'react';

interface WorkflowIssuesListProps {
  issues: Issue[];
  onNavigateToDocumentExplorer: (lineRange?: [number, number]) => void;
}

/**
 * The issues one assessment reported, or an all-clear when it found nothing.
 *
 * Passing checks (severity `none`) are collapsed behind a disclosure, so an
 * assessment that verified 717 abbreviations and flagged 3 reads as three
 * issues — and does not mount 717 cards to say so.
 */
export function WorkflowIssuesList({ issues, onNavigateToDocumentExplorer }: WorkflowIssuesListProps) {
  const [showInformational, setShowInformational] = useState(false);
  // Empty means no filter, matching the document explorer's severity toggles.
  const [severityFilter, setSeverityFilter] = useState<SeverityEnum[]>([]);

  const realIssues = issues.filter((i) => i.severity !== SeverityEnum.None);
  const informational = issues.filter((i) => i.severity === SeverityEnum.None);
  const visibleIssues =
    severityFilter.length === 0 ? realIssues : realIssues.filter((i) => severityFilter.includes(i.severity));
  const isFiltered = visibleIssues.length !== realIssues.length;

  const handleSelect = (issue: Issue) => {
    if (typeof issue.start_line === 'number' && typeof issue.end_line === 'number') {
      onNavigateToDocumentExplorer([issue.start_line, issue.end_line]);
    } else {
      onNavigateToDocumentExplorer();
    }
  };

  return (
    <>
      {realIssues.length === 0 ? (
        <Card className="border-green-200 bg-green-50/30 dark:bg-green-950/30 dark:border-green-900">
          <CardContent className="flex items-center gap-3 py-6">
            <div className="h-10 w-10 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center flex-shrink-0">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm font-medium">All Checks Passed</p>
              <p className="text-xs text-muted-foreground">No issues were found in the document.</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <section className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-medium text-muted-foreground">
              {isFiltered
                ? `${visibleIssues.length} of ${realIssues.length} Issues`
                : `${realIssues.length} Issue${realIssues.length !== 1 ? 's' : ''} Found`}
            </h3>
            <SeverityFilter value={severityFilter} onChange={setSeverityFilter} />
          </div>
          {visibleIssues.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">No issues match the selected severities.</p>
          ) : (
            <div className="space-y-2">
              {visibleIssues.map((issue) => (
                <DocumentIssueCard key={issue.id} issue={issue} onSelect={handleSelect} />
              ))}
            </div>
          )}
        </section>
      )}

      {informational.length > 0 && (
        <Collapsible open={showInformational} onOpenChange={setShowInformational} className="mt-4 space-y-2">
          <CollapsibleTrigger className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
            <ChevronDownIcon className={cn('size-3.5 transition-transform', !showInformational && '-rotate-90')} />
            {informational.length} Informational Item{informational.length !== 1 ? 's' : ''}
          </CollapsibleTrigger>
          <CollapsibleContent className="space-y-2">
            {informational.map((issue) => (
              <DocumentIssueCard key={issue.id} issue={issue} onSelect={handleSelect} />
            ))}
          </CollapsibleContent>
        </Collapsible>
      )}
    </>
  );
}
