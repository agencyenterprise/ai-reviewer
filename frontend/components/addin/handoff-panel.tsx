'use client';

import { Button } from '@/components/ui/button';
import { applyHandoff } from '@/lib/addin/apply-handoff';
import { AppliedItem, resultsOf } from '@/lib/addin/handoff-plan';
import { openSignOutDialog, signInInteractively, SignInMessage, ssoSignIn } from '@/lib/addin/sign-in';
import { getErrorMessage, isApiError } from '@/lib/api-error';
import {
  dismissApiMicrosoftWordHandoffsHandoffIdDismissedPost,
  HandoffView,
  listPendingApiMicrosoftWordHandoffsGet,
  reportAppliedApiMicrosoftWordHandoffsHandoffIdAppliedPost,
  startApiMicrosoftWordHandoffsHandoffIdStartedPost,
} from '@/lib/generated-api';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

/**
 * Comments and tracked changes someone asked Draft Detective for in Teams, waiting to
 * be written into this document. The bot cannot write a document itself, so the work
 * waits here until the person who asked opens it and chooses Apply.
 */
export function HandoffPanel() {
  const queryClient = useQueryClient();
  const [signedIn, setSignedIn] = useState<SignInMessage | null>(null);
  // Off once the API turned a token down or they signed out: nothing is tried silently
  // again until they choose to sign in.
  const [silentAllowed, setSilentAllowed] = useState(true);
  const [expired, setExpired] = useState(false);
  const documentUrl = typeof Office !== 'undefined' ? (Office.context.document?.url ?? '') : '';

  // Office single sign-on, without prompting: for most people this is the whole sign-in.
  const silent = useQuery({
    enabled: !signedIn && silentAllowed,
    queryKey: ['addin-sso'],
    queryFn: () => ssoSignIn(false),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
  const auth = signedIn ?? (silentAllowed ? (silent.data ?? null) : null);

  /**
   * The Authorization header for the next call. Office keeps its own token fresh, so
   * asking it again costs nothing while the token is valid and renews it when it is
   * not: a single sign-on session does not expire under the pane. A dialog token
   * cannot be renewed from here and lasts 15 minutes.
   */
  const authorize = async (): Promise<string> => {
    if (!auth) throw new Error('Not signed in');
    if (auth.via !== 'sso') return `Bearer ${auth.accessToken}`;
    return `Bearer ${(await ssoSignIn(false)).accessToken}`;
  };

  /** The API turned the token down, or Office would not renew it: sign in again. */
  const expire = () => {
    setSignedIn(null);
    setSilentAllowed(false);
    setExpired(true);
  };

  const signIn = useMutation({
    mutationFn: signInInteractively,
    onSuccess: (message) => {
      // Handoffs are cached per email, and two accounts can share one.
      queryClient.removeQueries({ queryKey: ['addin-handoffs'] });
      setSignedIn(message);
      setSilentAllowed(true);
      setExpired(false);
    },
  });

  // Office's own sign-in cannot be undone from an add-in, so signing out forgets the
  // token here and stops the silent sign-in; a dialog session is ended in a dialog.
  const signOut = useMutation({
    mutationFn: async () => {
      if (auth?.via === 'dialog') await openSignOutDialog();
    },
    onSettled: () => {
      setSignedIn(null);
      setSilentAllowed(false);
      setExpired(false);
      queryClient.removeQueries({ queryKey: ['addin-sso'] });
      queryClient.removeQueries({ queryKey: ['addin-handoffs'] });
    },
  });

  const pending = useQuery({
    enabled: !!auth && !!documentUrl,
    queryKey: ['addin-handoffs', auth?.email, documentUrl],
    queryFn: async () => {
      let authorization: string;
      try {
        authorization = await authorize();
      } catch (error) {
        expire();
        throw error;
      }
      try {
        return await listPendingApiMicrosoftWordHandoffsGet({
          query: { url: documentUrl },
          headers: { Authorization: authorization },
        });
      } catch (error) {
        if (isApiError(error, 401)) expire();
        throw error;
      }
    },
    retry: false,
  });

  if (!auth && silent.isFetching) return <Section>Signing in…</Section>;

  if (!auth) {
    return (
      <Section>
        <p className="text-xs text-muted-foreground">
          {expired
            ? 'Your sign-in expired. Sign in again to carry on.'
            : 'Asked Draft Detective for changes in Teams? Sign in to apply them.'}
        </p>
        <Button size="sm" variant="outline" onClick={() => signIn.mutate()} disabled={signIn.isPending}>
          {signIn.isPending ? 'Signing in…' : 'Sign in with Microsoft'}
        </Button>
        {signIn.error && <p className="text-xs text-red-500">{getErrorMessage(signIn.error, 'Sign-in failed')}</p>}
        {silent.error && (
          <p className="text-[11px] text-muted-foreground">
            Office single sign-on unavailable: {ssoFailure(silent.error)}
          </p>
        )}
      </Section>
    );
  }

  const account = (
    <div className="flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
      <span className="truncate">Signed in as {auth.email}</span>
      <Button
        size="sm"
        variant="ghost"
        className="h-6 px-2 text-[11px]"
        onClick={() => signOut.mutate()}
        disabled={signOut.isPending}
      >
        {signOut.isPending ? 'Signing out…' : 'Sign out'}
      </Button>
    </div>
  );

  if (pending.isLoading)
    return (
      <Section>
        {account}
        Checking for suggestions from Teams…
      </Section>
    );
  if (pending.error)
    return (
      <Section>
        {account}
        Could not check for suggestions from Teams.
      </Section>
    );

  const here = pending.data?.here ?? [];
  const elsewhere = pending.data?.elsewhere ?? [];

  return (
    <Section>
      {account}
      {here.map((handoff) => (
        <HandoffCard
          key={handoff.id}
          handoff={handoff}
          authorize={authorize}
          onExpired={expire}
          onDone={() => pending.refetch()}
        />
      ))}
      {here.length === 0 && elsewhere.length === 0 && (
        <p className="text-xs text-muted-foreground">Nothing waiting from Teams for {auth.email}.</p>
      )}
      {here.length === 0 && elsewhere.length > 0 && (
        <div className="text-xs text-muted-foreground">
          Suggestions are waiting for other documents:
          <ul className="list-disc pl-4">
            {elsewhere.map((handoff) => (
              <li key={handoff.id}>
                <a className="underline" href={handoff.document_url} target="_blank" rel="noreferrer">
                  {handoff.document_name}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
      {here.length === 0 && (
        <Button
          size="sm"
          variant="ghost"
          className="self-start"
          onClick={() => pending.refetch()}
          disabled={pending.isFetching}
        >
          {pending.isFetching ? 'Checking…' : 'Check again'}
        </Button>
      )}
    </Section>
  );
}

/** Office reports single sign-on failures as `{ code, message }`, not as an Error. */
function ssoFailure(error: unknown): string {
  const { code, message } = error as { code?: number; message?: string };
  return [code, message].filter(Boolean).join(' ') || String(error);
}

function Section({ children }: { children: React.ReactNode }) {
  return <div className="border-b p-3 flex flex-col gap-2 text-sm bg-card">{children}</div>;
}

type HandoffCardProps = {
  handoff: HandoffView;
  authorize: () => Promise<string>;
  onExpired: () => void;
  onDone: () => void;
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
function HandoffCard({ handoff, authorize, onExpired, onDone }: HandoffCardProps) {
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
    onSuccess: () => unreported.delete(handoff.id),
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
      return applyHandoff(handoff, authorize);
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

  if (written && report.isSuccess) return <AppliedSummary items={written} sent={report.data} onDone={onDone} />;
  if (written) {
    return (
      <div className="flex flex-col gap-2 text-xs">
        <p className="font-medium text-sm">Applied in Word.</p>
        {report.isError || report.isIdle ? (
          <>
            <p className="text-red-500">
              {report.isError ? 'The result could not be sent to Teams.' : 'The result has not reached Teams yet.'}{' '}
              Nothing needs applying again.
            </p>
            <Button size="sm" variant="outline" className="self-start" onClick={() => report.mutate(written)}>
              Send again
            </Button>
          </>
        ) : (
          <p className="text-muted-foreground">Sending the result to Teams…</p>
        )}
      </div>
    );
  }

  const busy = apply.isPending || dismiss.isPending;
  const interrupted = handoff.status === 'applying';
  return (
    <div className="flex flex-col gap-2">
      <p className="font-medium">
        From Teams: {comments.length} comment(s) and {edits.length} tracked change(s)
      </p>
      {interrupted ? (
        <p className="text-xs text-amber-600">
          Applying this started earlier and did not finish. Some of it may already be in the document, and applying
          again can add it twice. Check the document first, or dismiss it.
        </p>
      ) : (
        <p className="text-xs text-muted-foreground">
          Requested {new Date(handoff.created_at).toLocaleString()}. They are added as Draft Detective, and you accept
          or reject each change from the Review tab.
        </p>
      )}
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

function AppliedSummary({ items, sent, onDone }: { items: AppliedItem[]; sent: boolean; onDone: () => void }) {
  const missed = items.filter((item) => !item.applied);
  return (
    <div className="flex flex-col gap-1 text-xs">
      <p className="font-medium text-sm">
        Applied {items.length - missed.length} of {items.length}.
      </p>
      {!sent && <p className="text-muted-foreground">This was already closed, so nothing more was sent to Teams.</p>}
      {missed.map((item) => (
        <p key={item.index} className="text-muted-foreground">
          Not applied: {item.kind} on “{item.quote.slice(0, 60)}” {item.detail ? `(${item.detail})` : ''}
        </p>
      ))}
      <Button size="sm" variant="ghost" className="self-start" onClick={onDone}>
        Done
      </Button>
    </div>
  );
}
