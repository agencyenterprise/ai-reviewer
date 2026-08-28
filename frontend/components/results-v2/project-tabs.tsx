'use client';

import { TabType } from '@/components/results/constants';
import { cn } from '@/lib/utils';

export interface ProjectTab {
  id: TabType;
  label: string;
  /** Shown beside the label; omitted when there is nothing to count. */
  count?: number;
  /** Amber dot: this tab is waiting on the reader. */
  attention?: boolean;
}

interface ProjectTabsProps {
  tabs: ProjectTab[];
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

/**
 * The project's tab strip, sitting at the left of the header row with its
 * active marker riding the row's bottom border. The marker is what does the
 * explaining: a segmented control floating mid-row read as one more toolbar
 * widget, while a rule that touches the panel edge reads as the panel's own
 * label.
 */
export function ProjectTabs({ tabs, activeTab, onTabChange }: ProjectTabsProps) {
  return (
    <nav className="hidden h-full shrink-0 items-center lg:flex" aria-label="Project sections">
      {tabs.map((tab) => {
        const active = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            aria-current={active ? 'page' : undefined}
            className={cn(
              'relative flex h-full cursor-pointer items-center gap-1.5 px-3 text-[13px] transition-colors',
              // -bottom-px lands the marker on the header's own border, tying
              // the tab to the content underneath it.
              'after:bg-primary after:absolute after:inset-x-0 after:-bottom-px after:h-0.5 after:transition-opacity',
              active
                ? 'text-foreground font-medium after:opacity-100'
                : 'text-muted-foreground hover:text-foreground after:opacity-0',
            )}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span
                className={cn(
                  'font-mono text-[11px] tabular-nums',
                  active ? 'text-muted-foreground' : 'text-muted-foreground/70',
                )}
              >
                {tab.count}
              </span>
            )}
            {tab.attention && <span className="size-1.5 shrink-0 rounded-full bg-amber-500" />}
          </button>
        );
      })}
    </nav>
  );
}
