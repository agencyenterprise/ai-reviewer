'use client';

import { AppBar } from '@/components/results-v2/app-bar';
import { HomeView } from '@/components/results-v2/home/home-view';

/**
 * The v2 home page. Public: it is the page that explains what this is, so it has
 * to answer before anyone signs in.
 */
export default function HomePageV2() {
  return (
    <div className="bg-background text-foreground flex h-dvh flex-col">
      <AppBar />
      <HomeView />
    </div>
  );
}
