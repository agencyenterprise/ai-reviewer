'use client';

import { ProjectDetailed } from '@/lib/generated-api';
import { createContext, useContext } from 'react';
import { TabType } from './constants';

export interface ProjectViewContextValue {
  projectDetail: ProjectDetailed;
  /** When true, hides edit/action controls (for shared view) */
  readOnly: boolean;
  /** Currently displayed revision */
  selectedRevision?: number;
  /** Callback when user switches revision */
  onRevisionChange?: (revision: number) => void;
  /** Callback after a new revision is created, to follow it in the view */
  onRevisionCreated?: () => void;
  /** Switch to another tab, optionally landing on a URL hash (e.g. `#L5-12`) */
  navigateToTab: (tab: TabType, hash?: string) => void;
}

const ProjectViewContext = createContext<ProjectViewContextValue | undefined>(undefined);

export const ProjectViewProvider = ProjectViewContext.Provider;

export function useProjectView() {
  const context = useContext(ProjectViewContext);
  if (!context) {
    throw new Error('useProjectView must be used within a ProjectShell');
  }
  return context;
}
