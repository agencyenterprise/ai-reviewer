import { ErrorDetailsDialog } from '@/components/results/components/error-details-dialog';
import { WorkflowError } from '@/lib/generated-api';
import { isBlockingError } from '@/lib/workflow-state';
import { AlertTriangleIcon } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';

export interface ErrorsCardProps {
  errors: WorkflowError[];
  maxCount?: number;
}

interface MessageGroupProps {
  messages: WorkflowError[];
  title: string;
  className: string;
  maxCount: number;
  onInspect: (message: WorkflowError) => void;
}

function MessageGroup({ messages, title, className, maxCount, onInspect }: MessageGroupProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const visible = isExpanded ? messages : messages.slice(0, maxCount);
  const hasMore = messages.length > maxCount;

  return (
    <div className={`${className} p-4 rounded-lg text-sm`}>
      <h4 className="font-bold mb-2 flex items-center gap-2">
        <AlertTriangleIcon className="w-4 h-4" />
        {title}
      </h4>
      <div className="space-y-2">
        {visible.map((message, index) => (
          <div key={index} className="flex items-start justify-between gap-3">
            <pre className="whitespace-pre-wrap break-words min-w-0">
              <strong>{message.task_name}:</strong> {message.error}
            </pre>
            <Button variant="outline" size="sm" className="shrink-0 text-xs" onClick={() => onInspect(message)}>
              View details
            </Button>
          </div>
        ))}
      </div>
      {hasMore && (
        <div className="flex items-center justify-center">
          <Button variant="ghost" size="sm" onClick={() => setIsExpanded(!isExpanded)} className="mt-2 text-xs">
            {isExpanded ? 'Show less' : `Show more (${messages.length - maxCount} more)`}
          </Button>
        </div>
      )}
    </div>
  );
}

/**
 * Errors and warnings recorded by a workflow run. Warnings are failures the
 * workflow recovered from — the run still completed — so they are shown apart
 * from errors that cost the run output.
 */
export function ErrorsCard({ errors, maxCount = 3 }: ErrorsCardProps) {
  const [inspected, setInspected] = useState<WorkflowError | null>(null);
  const blocking = errors.filter(isBlockingError);
  const warnings = errors.filter((error) => !isBlockingError(error));

  return (
    <div className="space-y-3">
      {blocking.length > 0 && (
        <MessageGroup
          messages={blocking}
          title="Unexpected processing errors occurred while processing this chunk / document"
          className="bg-red-200/40"
          maxCount={maxCount}
          onInspect={setInspected}
        />
      )}
      {warnings.length > 0 && (
        <MessageGroup
          messages={warnings}
          title="This analysis completed, but some parts returned incomplete results"
          className="bg-amber-200/40"
          maxCount={maxCount}
          onInspect={setInspected}
        />
      )}
      <ErrorDetailsDialog error={inspected} onClose={() => setInspected(null)} />
    </div>
  );
}
