import type { ReasoningStep } from '@/components/assistant-ui/elements/reasoning-panel';

// A reasoning summary section opens with a bold heading on its own line. The
// backend joins a turn's sections with no separator, so one reasoning part can
// hold several: `**Title**\n\nbody**Next title**\n\nbody`.
const HEADING = /\*\*([^*\n]+)\*\*[ \t]*\n/g;

/** Splits reasoning summary text into the titled steps `ReasoningPanel` shows. */
export function reasoningSteps(text: string, fallbackTitle = 'Thinking'): ReasoningStep[] {
  const headings = [...text.matchAll(HEADING)];
  const steps: ReasoningStep[] = [];

  const lead = text.slice(0, headings[0]?.index ?? text.length).trim();
  if (lead) steps.push({ title: fallbackTitle, body: lead });

  headings.forEach((heading, i) => {
    const start = (heading.index ?? 0) + heading[0].length;
    const end = headings[i + 1]?.index ?? text.length;
    steps.push({ title: heading[1].trim(), body: text.slice(start, end).trim() });
  });

  return steps;
}
