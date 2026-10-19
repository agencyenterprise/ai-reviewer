import type { PaneCheck } from '@/lib/generated-api';

/**
 * The message a check is run with: its name, for the person reading the chat, and its
 * skill, which is what the agent looks up (`/skills/<skill>/SKILL.md`). The /chat page
 * runs a skill the same way, by naming it.
 */
export function checkMessage(check: Pick<PaneCheck, 'name' | 'skill'>): string {
  return `Run the ${check.name} check on this document (the "${check.skill}" skill).`;
}
