'use client';

import { Button } from '@/components/ui/button';
import { expiresAt, openSignOutDialog, signInInteractively, SignInMessage, ssoSignIn } from '@/lib/addin/sign-in';
import { getErrorMessage } from '@/lib/api-error';
import { QueryClient, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ReactNode, useState } from 'react';

/** What the signed-in parts of the pane get: who, and a header for the next call. */
export type AddinSession = {
  email: string;
  /**
   * The Authorization header for the next call. Office keeps its own token fresh, so
   * asking it again costs nothing while the token is valid and renews it when it is
   * not: a single sign-on session does not expire under the pane. A dialog token
   * cannot be renewed from here and lasts 15 minutes.
   */
  authorize: () => Promise<string>;
  /** The API turned the token down, or Office would not renew it: sign in again. */
  expire: () => void;
};

/** A token is renewed this long before it expires, so no call goes out with a stale one. */
const RENEW_BEFORE_MS = 2 * 60 * 1000;

/**
 * The single sign-on token in use, reused until it is close to expiring. Asking Office
 * for one is not free: in Word for the web it can show a "Waiting..." dialog, and an
 * Apply makes several calls. Held outside React state: a new token needs no re-render.
 */
class TokenCache {
  private token: string | null = null;

  /** The cached token, or ``fallback``, while it has more than a couple of minutes left. */
  fresh(fallback: string): string | null {
    const current = this.token ?? fallback;
    const expiry = expiresAt(current);
    return expiry !== null && expiry - Date.now() > RENEW_BEFORE_MS ? current : null;
  }

  set(token: string | null): void {
    this.token = token;
  }
}

/** Everything cached for one account: forgotten whenever the account may change. */
const ACCOUNT_QUERIES = new Set(['addin-handoffs', 'addin-chat', 'addin-suggestion']);

function forgetAccount(queryClient: QueryClient) {
  // Cached per email, and two accounts can share one.
  queryClient.removeQueries({ predicate: (query) => ACCOUNT_QUERIES.has(String(query.queryKey[0])) });
}

type AddinSignInProps = {
  /** What signing in is for, shown beside the button. */
  prompt: string;
  children: (session: AddinSession) => ReactNode;
};

/**
 * Signs the pane in as a Microsoft account and renders `children` once it is.
 *
 * Office single sign-on is tried first, without prompting: for most people that is the
 * whole sign-in. Otherwise a button signs in interactively, through Office or a dialog
 * (`lib/addin/sign-in.ts`).
 */
export function AddinSignIn({ prompt, children }: AddinSignInProps) {
  const queryClient = useQueryClient();
  const [signedIn, setSignedIn] = useState<SignInMessage | null>(null);
  // Off once the API turned a token down or they signed out: nothing is tried silently
  // again until they choose to sign in.
  const [silentAllowed, setSilentAllowed] = useState(true);
  const [expired, setExpired] = useState(false);

  const silent = useQuery({
    enabled: !signedIn && silentAllowed,
    queryKey: ['addin-sso'],
    queryFn: () => ssoSignIn(false),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
  const auth = signedIn ?? (silentAllowed ? (silent.data ?? null) : null);

  const [tokens] = useState(() => new TokenCache());
  const authorize = async (): Promise<string> => {
    if (!auth) throw new Error('Not signed in');
    if (auth.via !== 'sso') return `Bearer ${auth.accessToken}`;
    const current = tokens.fresh(auth.accessToken);
    if (current) return `Bearer ${current}`;
    let renewed: string;
    try {
      renewed = (await ssoSignIn(false)).accessToken;
    } catch (error) {
      // No HTTP call was made, so no 401 will end the session: end it here, so the pane
      // offers to sign in again instead of failing every call.
      expire();
      throw error;
    }
    tokens.set(renewed);
    return `Bearer ${renewed}`;
  };

  const expire = () => {
    tokens.set(null);
    setSignedIn(null);
    setSilentAllowed(false);
    setExpired(true);
  };

  const signIn = useMutation({
    mutationFn: signInInteractively,
    onSuccess: (message) => {
      tokens.set(null);
      forgetAccount(queryClient);
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
      tokens.set(null);
      setSignedIn(null);
      setSilentAllowed(false);
      setExpired(false);
      queryClient.removeQueries({ queryKey: ['addin-sso'] });
      forgetAccount(queryClient);
    },
  });

  if (!auth && silent.isFetching) return <Section>Signing in…</Section>;

  if (!auth) {
    return (
      <Section>
        <p className="text-xs text-muted-foreground">
          {expired ? 'Your sign-in expired. Sign in again to carry on.' : prompt}
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

  return (
    <>
      <div className="flex items-center justify-between gap-2 border-b px-3 py-1 text-[11px] text-muted-foreground">
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
      {children({ email: auth.email, authorize, expire })}
    </>
  );
}

/** Office reports single sign-on failures as `{ code, message }`, not as an Error. */
function ssoFailure(error: unknown): string {
  const { code, message } = error as { code?: number; message?: string };
  return [code, message].filter(Boolean).join(' ') || String(error);
}

export function Section({ children }: { children: ReactNode }) {
  return <div className="border-b p-3 flex flex-col gap-2 text-sm bg-card">{children}</div>;
}
