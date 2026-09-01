'use client';

import { AppBar } from '@/components/results/app-bar';
import { HomeView } from '@/components/results/home/home-view';

/**
 * The home page. Public: it is the page that explains what this is, so it has
 * to answer before anyone signs in.
 */
export default function HomePage() {
  return (
    <div className="bg-background text-foreground flex h-dvh flex-col">
      <AppBar />
      <HomeView />
    </div>
  );
}
