'use client';

import { TabType } from '@/components/results/constants';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { Check, ChevronDown } from 'lucide-react';

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
 *
 * Five tabs will not fit a narrow header, so below that width they collapse
 * into a menu naming the one you are on. Both are rendered and one is hidden
 * by CSS: neither holds state, so there is nothing for two copies to disagree
 * about, and the layout never flashes while a query resolves.
 */
export function ProjectTabs({ tabs, activeTab, onTabChange }: ProjectTabsProps) {
  const active = tabs.find((tab) => tab.id === activeTab) ?? tabs[0];

  return (
    <>
      <ProjectTabsMenu tabs={tabs} activeTab={activeTab} activeLabel={active?.label} onTabChange={onTabChange} />
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
    </>
  );
}

/** The same tabs as a menu, for headers too narrow to lay them out in a row. */
function ProjectTabsMenu({ tabs, activeTab, activeLabel, onTabChange }: ProjectTabsProps & { activeLabel?: string }) {
  const needsAttention = tabs.some((tab) => tab.attention && tab.id !== activeTab);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 max-w-64 min-w-0 flex-1 justify-start px-2 text-[13px] font-medium lg:hidden"
        >
          {/* Takes the room that is going spare and gives it back when the
              project's actions need it: "Document Explorer" is wide enough to
              push them off a phone screen on its own. */}
          <span className="truncate">{activeLabel}</span>
          {/* Something elsewhere is waiting; the strip would have shown its own
              dot, and folding the tabs away must not fold that away with them. */}
          {needsAttention && <span className="size-1.5 shrink-0 rounded-full bg-amber-500" />}
          <ChevronDown className="text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" className="w-56">
        {tabs.map((tab) => (
          <DropdownMenuItem key={tab.id} onSelect={() => onTabChange(tab.id)}>
            {tab.label}
            {tab.attention && <span className="size-1.5 shrink-0 rounded-full bg-amber-500" />}
            <span className="ml-auto flex items-center gap-2">
              {tab.count !== undefined && (
                <span className="font-mono text-[11px] tabular-nums text-muted-foreground">{tab.count}</span>
              )}
              {tab.id === activeTab && <Check className="size-3.5" />}
            </span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
