'use client';

import { Button } from '@/components/ui/button';
import { dialogSession, SIGN_IN_PATH, SignInMessage } from '@/lib/addin/sign-in';
import { officeReady } from '@/lib/addin/use-office-init';
import { useQuery } from '@tanstack/react-query';
import { getSession, signIn } from 'next-auth/react';

/**
 * Opened by the task pane as an Office dialog (see `lib/addin/sign-in.ts`), to hand it
 * a Draft Detective session token from a Microsoft sign-in.
 *
 * The token is a credential for the whole API, so it goes only to a pane on this
 * origin (`targetOrigin`), never on Office clients that cannot enforce that, and never
 * without a click: an existing session is handed back only after "Continue as …".
 * The exception is the return from a sign-in someone just started here by clicking,
 * recorded in this window's sessionStorage, which a page navigating here cannot set.
 */

// Set when "Sign in with Microsoft" is clicked in this window, consumed on return.
const SIGNING_IN = 'draft-detective-addin-signing-in';

type DialogState =
  | { step: 'redirecting' }
  | { step: 'unsupported' }
  | { step: 'confirm'; message: SignInMessage }
  | { step: 'sign-in' }
  | { step: 'handed-back' };

/** Whether this page is open as an Office dialog, with a pane to report back to. */
function inOfficeDialog(): boolean {
  return typeof Office !== 'undefined' && typeof Office.context?.ui?.messageParent === 'function';
}

function handBack(message: SignInMessage): void {
  Office.context.ui.messageParent(JSON.stringify(message), { targetOrigin: window.location.origin });
}

function takeSigningIn(): boolean {
  try {
    const started = window.sessionStorage.getItem(SIGNING_IN) === '1';
    window.sessionStorage.removeItem(SIGNING_IN);
    return started;
  } catch {
    return false;
  }
}

async function load(): Promise<DialogState> {
  await officeReady().catch(() => null);
  if (!inOfficeDialog()) {
    // Opened in a browser tab, not by the add-in: an app sign-in or sign-out that
    // inherited this page as Auth.js's remembered return address. Go to the app.
    window.location.replace('/');
    return { step: 'redirecting' };
  }
  if (!Office.context.requirements.isSetSupported('DialogOrigin', '1.1')) return { step: 'unsupported' };

  const session = await getSession();
  const message = dialogSession(session?.accessToken, session?.user?.email ?? undefined);
  if (!message) return { step: 'sign-in' };
  if (takeSigningIn()) {
    handBack(message);
    return { step: 'handed-back' };
  }
  return { step: 'confirm', message };
}

function startSignIn(): void {
  try {
    window.sessionStorage.setItem(SIGNING_IN, '1');
  } catch {
    // Without storage the return asks for one more click, which is fine.
  }
  // Always ask which account: signing in here is how someone switches accounts.
  void signIn('microsoft-entra-id', { callbackUrl: SIGN_IN_PATH }, { prompt: 'select_account' });
}

export default function AddinSignInPage() {
  const { data: state, isLoading } = useQuery({ queryKey: ['addin-sign-in'], queryFn: load, staleTime: Infinity });

  if (isLoading || !state || state.step === 'redirecting' || state.step === 'handed-back') {
    return <div className="p-4 text-center text-sm text-muted-foreground">Signing in…</div>;
  }

  if (state.step === 'unsupported') {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 text-center text-sm text-muted-foreground">
        This version of Office cannot sign in to Draft Detective safely from here. Update Office and try again.
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-3 p-4 text-center">
      <p className="text-sm text-muted-foreground max-w-xs">
        Sign in with the Microsoft account you use in Teams to see what Draft Detective prepared for this document.
      </p>
      {state.step === 'confirm' && (
        <Button
          onClick={() => {
            handBack(state.message);
          }}
        >
          Continue as {state.message.email}
        </Button>
      )}
      <Button variant={state.step === 'confirm' ? 'ghost' : 'default'} onClick={startSignIn}>
        {state.step === 'confirm' ? 'Use another account' : 'Sign in with Microsoft'}
      </Button>
    </div>
  );
}
