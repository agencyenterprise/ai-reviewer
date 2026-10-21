'use client';

import { Button } from '@/components/ui/button';
import { applyHandoff } from '@/lib/addin/apply-handoff';
import { AppliedItem, resultsOf } from '@/lib/addin/handoff-plan';
import { describeItems } from '@/lib/addin/item-counts';
import { getErrorMessage, isApiError } from '@/lib/api-error';
import {
  dismissApiMicrosoftWordHandoffsHandoffIdDismissedPost,
  HandoffComment,
  HandoffEdit,
  HandoffView,
  reportAppliedApiMicrosoftWordHandoffsHandoffIdAppliedPost,
  startApiMicrosoftWordHandoffsHandoffIdStartedPost,
} from '@/lib/generated-api';
import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';

/** Where a handoff came from, which changes only what the card says. */
export type HandoffSource = 'teams' | 'chat';

const WORDING: Record<HandoffSource, { title: string; destination: string }> = {
  teams: { title: 'From Teams', destination: 'Teams' },
  chat: { title: 'Suggested', destination: 'the chat' },
};

/** The fields of a handoff the card needs; the chat's suggestions have them too. */
export type HandoffCardItem = Pick<HandoffView, 'id' | 'status' | 'items' | 'created_at'>;

type HandoffCardProps = {
  handoff: HandoffCardItem;
  source: HandoffSource;
  authorize: () => Promise<string>;
  onExpired: () => void;
  onDone: () => void;
  /** Called once the result is reported, instead of showing it: the caller shows it. */
  onReported?: () => void;
};

/**
 * Results written into Word but not yet reported, by handoff. Kept outside the card
 * because an expired sign-in unmounts it: after signing in again the report can still be
 * sent, instead of the handoff coming back as interrupted.
 */
const unreported = new Map<string, AppliedItem[]>();

/**
 * One handoff: Apply claims it on the server, writes it, then reports the results.
 *
 * Claiming first means a run that never reports back (a closed pane, an expired token,
 * a network error) leaves the handoff `applying` rather than `pending`, so it comes back
 * with a warning instead of an Apply that would write every comment twice. A report
 * that fails after the writes succeeded is kept here and can be sent again on its own.
 */
export function HandoffCard({ handoff, source, authorize, onExpired, onDone, onReported }: HandoffCardProps) {
  const wording = WORDING[source];
  const comments = handoff.items.comments ?? [];
  const edits = handoff.items.edits ?? [];
  const [written, setWrittenState] = useState<AppliedItem[] | null>(() => unreported.get(handoff.id) ?? null);
  const setWritten = (items: AppliedItem[]) => {
    unreported.set(handoff.id, items);
    setWrittenState(items);
  };
  const expireOn401 = (error: Error) => {
    if (isApiError(error, 401)) onExpired();
  };

  // Resolves false when the handoff is already closed (an earlier report landed but its
  // answer was lost, or it expired): there is nothing left to send, so it is not an error.
  const report = useMutation({
    mutationFn: async (items: AppliedItem[]): Promise<boolean> => {
      try {
        await reportAppliedApiMicrosoftWordHandoffsHandoffIdAppliedPost({
          path: { handoff_id: handoff.id },
          body: { results: resultsOf(items) },
          headers: { Authorization: await authorize() },
        });
        return true;
      } catch (error) {
        if (isApiError(error, 404)) return false;
        throw error;
      }
    },
    onSuccess: () => {
      unreported.delete(handoff.id);
      onReported?.();
    },
    onError: expireOn401,
  });

  const apply = useMutation({
    mutationFn: async (): Promise<AppliedItem[]> => {
      if (handoff.status === 'pending') {
        try {
          await startApiMicrosoftWordHandoffsHandoffIdStartedPost({
            path: { handoff_id: handoff.id },
            headers: { Authorization: await authorize() },
          });
        } catch (error) {
          if (isApiError(error, 404)) {
            onDone();
            throw new Error('This was already applied, or is being applied somewhere else.');
          }
          throw error;
        }
      }
      return applyHandoff(handoff);
    },
    onSuccess: (items) => {
      setWritten(items);
      report.mutate(items);
    },
    onError: expireOn401,
  });

  const dismiss = useMutation({
    mutationFn: async () =>
      dismissApiMicrosoftWordHandoffsHandoffIdDismissedPost({
        path: { handoff_id: handoff.id },
        headers: { Authorization: await authorize() },
      }),
    onSuccess: onDone,
    onError: expireOn401,
  });

  if (written && report.isSuccess) {
    if (onReported) return null;
    return <AppliedSummary items={written} sent={report.data} destination={wording.destination} onDone={onDone} />;
  }
  if (written) {
    return (
      <div className="flex flex-col gap-2 text-xs">
        <p className="font-medium text-sm">Applied in Word.</p>
        {report.isError || report.isIdle ? (
          <>
            <p className="text-red-500">
              {report.isError
                ? `The result could not be sent to ${wording.destination}.`
                : `The result has not reached ${wording.destination} yet.`}{' '}
              Nothing needs applying again.
            </p>
            <Button size="sm" variant="outline" className="self-start" onClick={() => report.mutate(written)}>
              Send again
            </Button>
          </>
        ) : (
          <p className="text-muted-foreground">Sending the result to {wording.destination}…</p>
        )}
      </div>
    );
  }

  const busy = apply.isPending || dismiss.isPending;
  // `applying` on the server is this card's own run while Apply is pending here; only a
  // run that is not this pane's, or one that ended without reporting, is interrupted.
  const interrupted = handoff.status === 'applying' && !apply.isPending;
  return (
    <div className="flex flex-col gap-2">
      <p className="font-medium">
        {wording.title}: {describeItems(comments.length, edits.length)}
      </p>
      {interrupted ? (
        <p className="text-xs text-amber-600">
          Applying this started earlier and did not finish. Some of it may already be in the document, and applying
          again can add it twice. Check the document first, or dismiss it.
        </p>
      ) : (
        <p className="text-xs text-muted-foreground">
          Requested {new Date(handoff.created_at).toLocaleString()}. They are added under your name, comments starting
          “Draft Detective:”, and you accept or reject each change from the Review tab.
        </p>
      )}
      <ItemList comments={comments} edits={edits} />
      <div className="flex gap-2">
        <Button size="sm" variant={interrupted ? 'outline' : 'default'} onClick={() => apply.mutate()} disabled={busy}>
          {apply.isPending ? 'Applying…' : interrupted ? 'Apply anyway' : 'Apply'}
        </Button>
        <Button size="sm" variant="ghost" onClick={() => dismiss.mutate()} disabled={busy}>
          Dismiss
        </Button>
      </div>
      {(apply.error || dismiss.error) && (
        <p className="text-xs text-red-500">{getErrorMessage(apply.error ?? dismiss.error, 'Something went wrong')}</p>
      )}
    </div>
  );
}

/** What Apply would write, folded away: the counts are enough to decide most of the time. */
function ItemList({ comments, edits }: { comments: HandoffComment[]; edits: HandoffEdit[] }) {
  if (comments.length + edits.length === 0) return null;
  return (
    <details className="text-xs">
      <summary className="cursor-pointer text-muted-foreground">Show what would be added</summary>
      <ul className="mt-1 flex flex-col gap-1.5">
        {edits.map((edit, index) => (
          <li key={`edit-${index}`}>
            <span className="line-through text-muted-foreground">{edit.quote}</span>{' '}
            {edit.replacement ? <span>→ {edit.replacement}</span> : <span className="italic">(deleted)</span>}
          </li>
        ))}
        {comments.map((comment, index) => (
          <li key={`comment-${index}`}>
            <span className="text-muted-foreground">“{comment.quote}”</span>: {comment.comment}
          </li>
        ))}
      </ul>
    </details>
  );
}

type AppliedSummaryProps = {
  items: AppliedItem[];
  /** False when the handoff was already closed, so nothing more was sent. */
  sent: boolean;
  destination: string;
  onDone?: () => void;
};

export function AppliedSummary({ items, sent, destination, onDone }: AppliedSummaryProps) {
  const missed = items.filter((item) => !item.applied);
  return (
    <div className="flex flex-col gap-1 text-xs">
      <p className="font-medium text-sm">
        Applied {items.length - missed.length} of {items.length}.
      </p>
      {!sent && (
        <p className="text-muted-foreground">This was already closed, so nothing more was sent to {destination}.</p>
      )}
      {missed.map((item) => (
        <p key={item.index} className="text-muted-foreground">
          Not applied: {item.kind} on “{item.quote.slice(0, 60)}” {item.detail ? `(${item.detail})` : ''}
        </p>
      ))}
      {onDone && (
        <Button size="sm" variant="ghost" className="self-start" onClick={onDone}>
          Done
        </Button>
      )}
    </div>
  );
}
