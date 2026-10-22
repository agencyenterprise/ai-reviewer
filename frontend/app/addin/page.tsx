'use client';

import { AddinPane } from '@/components/addin/addin-pane';
import { AddinSignIn } from '@/components/addin/addin-sign-in';
import { useOfficeInit } from '@/lib/addin/use-office-init';

export default function AddinPage() {
  const { isInitialized } = useOfficeInit();

  if (!isInitialized) return <div className="p-4 text-center">Loading Add-in...</div>;

  return (
    <div className="flex flex-col h-screen bg-card">
      <AddinSignIn prompt="Sign in to chat with Draft Detective about this document.">
        {(session) => <AddinPane session={session} />}
      </AddinSignIn>
    </div>
  );
}
