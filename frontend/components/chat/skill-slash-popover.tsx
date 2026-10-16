'use client';

import { useSkillCommands } from '@/lib/skill-commands';
import {
  ComposerPrimitive,
  unstable_useSlashCommandAdapter,
  useAui,
  type Unstable_SlashCommand,
} from '@assistant-ui/react';
import { useMemo, type FC } from 'react';

/**
 * The composer's `/` menu: one command per skill. Render it inside
 * `ComposerPrimitive.Unstable_TriggerPopoverRoot`, next to the composer input.
 */
export const SkillSlashPopover: FC = () => {
  const aui = useAui();

  // `execute` pre-fills the composer with an explicit instruction so the agent
  // reads and runs that skill (from the skills mounted in its filesystem); the
  // user can then paste the document and send.
  const skillCommands = useSkillCommands();
  const commands = useMemo<Unstable_SlashCommand[]>(
    () =>
      skillCommands.map((command) => ({
        id: command.id,
        description: command.description,
        execute: () => {
          // Replace the composer with an explicit skill instruction. We set it
          // unconditionally (rather than appending to the current text) because
          // the trigger-strip runs in the same tick and reading it back races.
          aui.composer().setText(`Please run the "${command.id}" skill.\n\n`);
        },
      })),
    [aui, skillCommands],
  );

  const slash = unstable_useSlashCommandAdapter({ commands, removeOnExecute: true });

  return (
    <ComposerPrimitive.Unstable_TriggerPopover
      char="/"
      adapter={slash.adapter}
      className="absolute bottom-full left-0 z-50 mb-2 max-h-72 w-full overflow-y-auto rounded-xl border bg-popover p-1 text-popover-foreground shadow-md"
    >
      <ComposerPrimitive.Unstable_TriggerPopover.Action {...slash.action} />
      <ComposerPrimitive.Unstable_TriggerPopoverItems>
        {(items) =>
          items.map((item, index) => (
            <ComposerPrimitive.Unstable_TriggerPopoverItem key={item.id} item={item} index={index} asChild>
              <button
                type="button"
                className="flex w-full flex-col items-start gap-0.5 rounded-lg px-3 py-2 text-left text-sm outline-none data-[highlighted=true]:bg-accent"
              >
                <span className="font-medium">{item.label}</span>
                {item.description && (
                  <span className="line-clamp-2 text-muted-foreground text-xs">{item.description}</span>
                )}
              </button>
            </ComposerPrimitive.Unstable_TriggerPopoverItem>
          ))
        }
      </ComposerPrimitive.Unstable_TriggerPopoverItems>
    </ComposerPrimitive.Unstable_TriggerPopover>
  );
};
