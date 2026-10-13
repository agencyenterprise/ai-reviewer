'use client';

import { HtmlReportFrame, HtmlReportFrameHandle } from '@/components/results/components/html-report-frame';
import { TabError, TabLoading } from '@/components/results/tab-status';
import { AgentTranscript } from '@/components/workflows/results/agent-transcript';
import { FileTypeIcon } from '@/components/shared/file-type-icon';
import { Button } from '@/components/ui/button';
import { StatusIndicator } from '@/components/ui/status-indicator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  FileListItem,
  ReviewAssistantRequestSummary,
  ReviewAssistantState,
  WorkflowErrorSeverity,
  WorkflowRunStatus,
} from '@/lib/generated-api';
import { useWorkflowRunDetail } from '@/lib/hooks/use-project-data';
import { getDisplayStatus, isWorkflowProcessing } from '@/lib/workflow-state';
import { format } from 'date-fns';
import { Download, Loader2, X } from 'lucide-react';
import { useRef, useState } from 'react';
import { outputTitle } from './outputs';
import { useCancelReviewAssistantRequest } from './use-review-assistant';

interface RequestViewProps {
  projectId: string;
  request: ReviewAssistantRequestSummary;
  projectFiles: FileListItem[];
  readOnly: boolean;
}

const DOCUMENTS_TAB = 'documents';
const MESSAGES_TAB = 'messages';

/** One request: what was asked for, what it read, and what it wrote. */
export function RequestView({ projectId, request, projectFiles, readOnly }: RequestViewProps) {
  const summary = { run: request.run, errors: request.errors ?? [] };
  const { data: detail, error, isPlaceholderData } = useWorkflowRunDetail(projectId, summary);
  const cancel = useCancelReviewAssistantRequest(projectId);
  const processing = isWorkflowProcessing(summary);
  const status = getDisplayStatus(summary);

  const state = detail?.state as ReviewAssistantState | undefined;

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start gap-3 border-b pb-4">
        <div className="min-w-0 flex-1">
          <h1 className="text-base font-semibold tracking-tight">{request.outputs.map(outputTitle).join(', ')}</h1>
          <p className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
            <StatusIndicator status={status} />
            <span>Started {format(new Date(request.run.created_at), 'MMM d, h:mm a')}</span>
          </p>
        </div>
        {processing && !readOnly && (
          <Button size="sm" variant="outline" onClick={() => cancel.mutate(request.run.id)} disabled={cancel.isPending}>
            <X className="size-3.5" />
            Cancel
          </Button>
        )}
      </header>

      {error ? (
        <TabError what="this request" error={error} />
      ) : processing ? (
        <Working request={request} projectFiles={projectFiles} />
      ) : status === WorkflowRunStatus.Failed || status === WorkflowRunStatus.Cancelled ? (
        <Stopped
          message={
            status === WorkflowRunStatus.Cancelled
              ? 'This request was cancelled.'
              : (request.run.failure_message ?? 'This request failed before it could finish. Try it again.')
          }
        />
      ) : !state || isPlaceholderData ? (
        // The run just finished and its new state is still on its way: the one
        // held over from while it ran has no reports yet.
        <TabLoading label="Loading results..." />
      ) : state.guard_message ? (
        <>
          <SkippedDocuments request={request} />
          <Stopped message={state.guard_message} />
        </>
      ) : (
        <>
          <SkippedDocuments request={request} />
          <Results state={state} request={request} projectFiles={projectFiles} />
        </>
      )}
    </div>
  );
}

function Working({ request, projectFiles }: { request: ReviewAssistantRequestSummary; projectFiles: FileListItem[] }) {
  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3 rounded-md border border-dashed px-4 py-5">
        <Loader2 className="mt-0.5 size-4 shrink-0 animate-spin text-muted-foreground" />
        <p className="text-[13px] leading-relaxed text-muted-foreground">
          Reading every document, working out which is which, and writing{' '}
          {request.outputs.length === 1 ? 'the output' : `all ${request.outputs.length} outputs`}. This can take a
          while. You can leave this page; the results will be here.
        </p>
      </div>
      <DocumentList request={request} projectFiles={projectFiles} />
    </div>
  );
}

/** Documents the run could not read and went ahead without, so the author can retry. */
function SkippedDocuments({ request }: { request: ReviewAssistantRequestSummary }) {
  const warnings = (request.errors ?? []).filter((error) => error.severity === WorkflowErrorSeverity.Warning);
  if (warnings.length === 0) return null;
  return (
    <ul className="space-y-1 rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-xs leading-relaxed text-amber-900 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
      {warnings.map((warning) => (
        <li key={warning.error}>{warning.error}</li>
      ))}
    </ul>
  );
}

function Stopped({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-dashed px-4 py-6 text-center text-[13px] leading-relaxed text-muted-foreground">
      {message}
    </div>
  );
}

function Results({
  state,
  request,
  projectFiles,
}: {
  state: ReviewAssistantState;
  request: ReviewAssistantRequestSummary;
  projectFiles: FileListItem[];
}) {
  const reports = state.reports ?? [];
  // Derived, not seeded once: reports may arrive after this mounts.
  const [picked, setTab] = useState<string | null>(null);
  const tab = picked ?? reports[0]?.output ?? DOCUMENTS_TAB;
  const frameRef = useRef<HtmlReportFrameHandle>(null);
  const missing = request.outputs.filter((output) => !reports.some((report) => report.output === output));

  return (
    <Tabs value={tab} onValueChange={setTab} className="gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <TabsList>
          {reports.map((report) => (
            <TabsTrigger key={report.output} value={report.output}>
              {outputTitle(report.output)}
            </TabsTrigger>
          ))}
          <TabsTrigger value={DOCUMENTS_TAB}>Documents</TabsTrigger>
          <TabsTrigger value={MESSAGES_TAB}>Messages</TabsTrigger>
        </TabsList>
        {/* Only beside a report: the other tabs unmount its frame, which would
            leave this printing nothing. */}
        {reports.some((report) => report.output === tab) && (
          <Button variant="outline" size="sm" onClick={() => frameRef.current?.print()}>
            <Download className="size-4" />
            Download PDF
          </Button>
        )}
      </div>

      {missing.length > 0 && (
        <p className="text-xs text-muted-foreground">
          Not written this time: {missing.map(outputTitle).join(', ')}. Start a new request to try again.
        </p>
      )}

      {reports.map((report) => (
        <TabsContent key={report.output} value={report.output}>
          {tab === report.output && (
            <HtmlReportFrame ref={frameRef} html={report.report_html} title={outputTitle(report.output)} />
          )}
        </TabsContent>
      ))}
      <TabsContent value={DOCUMENTS_TAB}>
        <DocumentList request={request} projectFiles={projectFiles} state={state} />
      </TabsContent>
      <TabsContent value={MESSAGES_TAB}>
        <AgentTranscript messages={state.messages ?? []} />
      </TabsContent>
    </Tabs>
  );
}

/**
 * The documents a request read, and what the Review Assistant took each one
 * to be. That reading is the author's check: a draft taken for the wrong
 * version is what to catch before trusting the outputs.
 */
function DocumentList({
  request,
  projectFiles,
  state,
}: {
  request: ReviewAssistantRequestSummary;
  projectFiles: FileListItem[];
  state?: ReviewAssistantState;
}) {
  const byId = new Map(projectFiles.map((file) => [file.id, file]));
  const inputs = state?.inputs ?? [];
  const readings = new Map((state?.input_readings ?? []).map((reading) => [reading.folder, reading]));

  return (
    <ul className="divide-y rounded-md border">
      {request.input_file_ids.map((fileId) => {
        const file = byId.get(fileId);
        const input = inputs.find((entry) => entry.file_id === fileId);
        const reading = input ? readings.get(input.folder) : undefined;
        const markup = [
          input?.comment_count ? `${input.comment_count} comment${input.comment_count === 1 ? '' : 's'}` : null,
          input?.tracked_change_count
            ? `${input.tracked_change_count} tracked change${input.tracked_change_count === 1 ? '' : 's'}`
            : null,
        ].filter(Boolean);
        return (
          <li key={fileId} className="flex items-start gap-3 px-3 py-2.5">
            <FileTypeIcon fileType={file?.file_type} />
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px]">{file?.file_name ?? input?.file_name ?? 'A file since removed'}</p>
              {markup.length > 0 && (
                <p className="text-[11px] text-muted-foreground">Word file with {markup.join(' and ')}</p>
              )}
              {reading?.note && <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">{reading.note}</p>}
            </div>
            {reading?.role && (
              <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 text-[11px] font-medium">
                {reading.role}
                {reading.reviewer ? ` · ${reading.reviewer}` : ''}
              </span>
            )}
          </li>
        );
      })}
    </ul>
  );
}
