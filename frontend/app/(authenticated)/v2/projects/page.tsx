'use client';

import { AppBar } from '@/components/results-v2/app-bar';
import { ProjectsView } from '@/components/results-v2/projects/projects-view';

/**
 * The projects list in the v2 frame. Same chrome as a project itself — the
 * application row, then a rail beside the work — so moving from the list into a
 * project does not change the furniture around you.
 */
export default function ProjectsPageV2() {
  return (
    <div className="bg-background text-foreground flex h-dvh flex-col">
      <AppBar />
      <ProjectsView />
    </div>
  );
}
