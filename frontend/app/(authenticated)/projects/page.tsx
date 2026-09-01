'use client';

import { AppBar } from '@/components/results/app-bar';
import { ProjectsView } from '@/components/results/projects/projects-view';

/**
 * The projects list. Same chrome as a project itself — the application row,
 * then the work below it — so moving from the list into a project does not
 * change the furniture around you.
 */
export default function ProjectsPage() {
  return (
    <div className="bg-background text-foreground flex h-dvh flex-col">
      <AppBar />
      <ProjectsView />
    </div>
  );
}
