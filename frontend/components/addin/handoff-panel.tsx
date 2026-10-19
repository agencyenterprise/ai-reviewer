'use client';

import { AddinSession, AddinSignIn, Section } from '@/components/addin/addin-sign-in';
import { HandoffCard } from '@/components/addin/handoff-card';
import { Button } from '@/components/ui/button';
import { isApiError } from '@/lib/api-error';
import { listPendingApiMicrosoftWordHandoffsGet } from '@/lib/generated-api';
import { useQuery } from '@tanstack/react-query';

export const TEAMS_SIGN_IN_PROMPT = 'Asked Draft Detective for changes in Teams? Sign in to apply them.';

/** The handoffs list on its own, signing in first: what the pane showed before its chat. */
export function HandoffPanel() {
  return <AddinSignIn prompt={TEAMS_SIGN_IN_PROMPT}>{(session) => <HandoffList session={session} />}</AddinSignIn>;
}

/**
 * Comments and tracked changes someone asked Draft Detective for in Teams, waiting to
 * be written into this document. The bot cannot write a document itself, so the work
 * waits here until the person who asked opens it and chooses Apply.
 */
export function HandoffList({ session }: { session: AddinSession }) {
  const { email, authorize, expire } = session;
  const documentUrl = typeof Office !== 'undefined' ? (Office.context.document?.url ?? '') : '';

  const pending = useQuery({
    enabled: !!documentUrl,
    queryKey: ['addin-handoffs', email, documentUrl],
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

  if (pending.isLoading) return <Section>Checking for suggestions from Teams…</Section>;
  if (pending.error) return <Section>Could not check for suggestions from Teams.</Section>;

  const here = pending.data?.here ?? [];
  const elsewhere = pending.data?.elsewhere ?? [];

  return (
    <Section>
      {here.map((handoff) => (
        <HandoffCard
          key={handoff.id}
          handoff={handoff}
          source="teams"
          authorize={authorize}
          onExpired={expire}
          onDone={() => pending.refetch()}
        />
      ))}
      {here.length === 0 && elsewhere.length === 0 && (
        <p className="text-xs text-muted-foreground">Nothing waiting from Teams for {email}.</p>
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
