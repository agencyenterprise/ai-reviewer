'use client';

import { Clock, History, LucideIcon, PlayIcon } from 'lucide-react';
import { ReactNode } from 'react';
import { SectionTitle } from '../help-primitives';

/** What running one sets in motion, once you have picked from the list. */
const MECHANICS: { icon: LucideIcon; title: string; body: string }[] = [
  {
    icon: PlayIcon,
    title: 'They run in the background, and in order',
    body: 'Pick as many as you like and carry on reading. Some need another to finish first — the document has to be converted before anything can be read — so they queue themselves rather than asking you to sequence them.',
  },
  {
    icon: History,
    title: 'Re-running one replaces what the explorer shows',
    body: 'The findings from the previous run are archived rather than deleted: the run stays in that assessment’s history, and you can open it to read what it said.',
  },
  {
    icon: Clock,
    title: 'Every run records what it cost',
    body: 'How long it took and what it spent are kept beside the result, so an expensive assessment is an informed choice rather than a surprise.',
  },
];

/**
 * What an assessment is and what running one costs you. Deliberately not a
 * catalogue: the list of assessments, with each one's description, is a click
 * away in the dialog that starts them, and repeating it here would be a second
 * copy to keep true.
 */
export function AssessmentsTopic() {
  return (
    <div className="space-y-5">
      <section>
        <SectionTitle>One question each</SectionTitle>
        <p className="text-foreground/80 leading-relaxed">
          An assessment reads your draft looking for one kind of problem, and reports what it finds as{' '}
          <strong className="text-foreground font-medium">issues in the document explorer</strong>, anchored to the
          lines they are about. Nothing is changed in your document — an assessment only reads.
        </p>
      </section>

      <section>
        <SectionTitle>Running them</SectionTitle>
        <p className="text-foreground/80 mb-2 leading-relaxed">
          <strong className="text-foreground font-medium">Run assessments</strong> in the header opens the list at any
          time, from any tab. The Assessments tab is where their results are read.
        </p>
        <div className="space-y-2">
          {MECHANICS.map((item) => (
            <Mechanic key={item.title} icon={item.icon} title={item.title}>
              {item.body}
            </Mechanic>
          ))}
        </div>
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          One assessment waits for you rather than for another assessment: Claim Reference Validation needs the source
          documents behind your citations, and holds until you say they are ready.
        </p>
      </section>
    </div>
  );
}

function Mechanic({ icon: Icon, title, children }: { icon: LucideIcon; title: string; children: ReactNode }) {
  return (
    <div className="flex gap-2.5 rounded-md border p-2.5">
      <Icon className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" aria-hidden />
      <div className="min-w-0">
        <p className="text-xs font-medium">{title}</p>
        <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">{children}</p>
      </div>
    </div>
  );
}
