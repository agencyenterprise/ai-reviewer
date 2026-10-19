'use client';

import { TooltipIconButton } from '@/components/assistant-ui/elements/tooltip-icon-button';
import { SlashCommandPopover } from '@/components/chat/skill-slash-popover';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { checkMessage } from '@/lib/addin/checks';
import type { PaneCheck } from '@/lib/generated-api';
import { useAui, useAuiState, type Unstable_SlashCommand } from '@assistant-ui/react';
import { ListChecksIcon } from 'lucide-react';
import { useMemo, useState, type FC } from 'react';
import { usePaneChecks } from './use-pane-checks';

/** Sends a check as a message straight away: the document is already there to run it on. */
function useRunCheck(): (check: PaneCheck) => void {
  const aui = useAui();
  return (check) => {
    aui.composer().setText('');
    aui.thread().append({ role: 'user', content: [{ type: 'text', text: checkMessage(check) }] });
  };
}

/** The composer's `/` menu in the pane: the checks, which run as soon as one is picked. */
export const CheckSlashPopover: FC = () => {
  const checks = usePaneChecks();
  const run = useRunCheck();
  // None while an answer is running: picking one would start a second turn at once, as
  // the list button's being disabled prevents.
  const isRunning = useAuiState((s) => s.thread.isRunning);
  const commands = useMemo<Unstable_SlashCommand[]>(
    () =>
      isRunning
        ? []
        : checks.map((check) => ({
            id: check.skill,
            label: check.name,
            description: check.description,
            execute: () => run(check),
          })),
    // `run` is rebuilt every render and only closes over the runtime, which is stable.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [checks, isRunning],
  );
  return <SlashCommandPopover commands={commands} />;
};

/** The list button beside the composer: every check by name, searchable, the experimental ones apart. */
export const ChecksMenu: FC = () => {
  const checks = usePaneChecks();
  const run = useRunCheck();
  const [open, setOpen] = useState(false);
  const isRunning = useAuiState((s) => s.thread.isRunning);
  const groups = [
    { heading: 'Checks', items: checks.filter((check) => !check.experimental) },
    { heading: 'Experimental', items: checks.filter((check) => check.experimental) },
  ].filter((group) => group.items.length > 0);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <TooltipIconButton
          tooltip="Run a check"
          side="bottom"
          type="button"
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-foreground size-7 rounded-full"
          aria-label="Run a check"
          disabled={isRunning || checks.length === 0}
        >
          <ListChecksIcon className="size-4" />
        </TooltipIconButton>
      </PopoverTrigger>
      <PopoverContent side="top" align="start" className="w-[min(20rem,calc(100vw-1.5rem))] p-0">
        <Command>
          <CommandInput placeholder="Find a check" />
          <CommandList className="max-h-72">
            <CommandEmpty>No check by that name.</CommandEmpty>
            {groups.map((group) => (
              <CommandGroup key={group.heading} heading={group.heading}>
                {group.items.map((check) => (
                  <CommandItem
                    key={check.skill}
                    value={`${check.name} ${check.skill}`}
                    onSelect={() => {
                      setOpen(false);
                      run(check);
                    }}
                    className="flex flex-col items-start gap-0.5"
                  >
                    <span className="font-medium">{check.name}</span>
                    <span className="line-clamp-2 text-xs text-muted-foreground">{check.description}</span>
                  </CommandItem>
                ))}
              </CommandGroup>
            ))}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
};
