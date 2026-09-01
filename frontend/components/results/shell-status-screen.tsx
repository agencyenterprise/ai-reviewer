'use client';

import { ReactNode } from 'react';
import { AppBar } from './app-bar';

/**
 * The application row over a centred panel, for the states that exist before
 * the project does: loading, denied, missing. The row renders either way, so a
 * slow load is never a blank page.
 */
export function ShellStatusScreen({ children }: { children: ReactNode }) {
  return (
    <div className="bg-background text-foreground flex h-dvh flex-col">
      <AppBar />
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="max-w-sm text-center">{children}</div>
      </div>
    </div>
  );
}
