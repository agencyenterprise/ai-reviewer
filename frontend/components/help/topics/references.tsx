'use client';

import { ScanSearch } from 'lucide-react';
import { SectionTitle, TopicLink } from '../help-primitives';
import { HelpTopicBodyProps } from '../topics';

/**
 * An invented entry, broken into the parts a citation check compares against
 * the published record. A real reference from the reader's own bibliography
 * would make the point better, but this topic is read from anywhere — including
 * before extraction has run.
 */
const PARTS: { label: string; value: string }[] = [
  { label: 'Author', value: 'Sandoval, R., & Okoye, T.' },
  { label: 'Year', value: '(2023).' },
  { label: 'Title', value: 'Compute trends in large-scale training.' },
  { label: 'Publisher', value: 'Journal of Applied Computing, 14(2), 88–104.' },
];

/**
 * What a reference is and where it comes from. Deliberately stops at the edge
 * of the bibliography: what happens once you have the document a reference
 * names is the source-files topic, one entry down.
 */
export function ReferencesTopic({ onOpenTopic }: HelpTopicBodyProps) {
  return (
    <div className="space-y-5">
      <section>
        <SectionTitle>Where they come from</SectionTitle>
        <p className="text-foreground/80 leading-relaxed">
          A reference is one entry in your bibliography. Draft Detective{' '}
          <strong className="text-foreground font-medium">pulls every one of them out of your draft by itself</strong> —
          you do not type them in or upload a list — and the References tab is where they are listed, in the order they
          appear in the document.
        </p>
        <p className="text-foreground/80 mt-2 leading-relaxed">
          Extraction runs on its own as soon as the document is processed, and again on each new{' '}
          <TopicLink to="revisions" onOpenTopic={onOpenTopic}>
            revision
          </TopicLink>
          , so the list always describes the draft you are reading.
        </p>
      </section>

      <section>
        <SectionTitle>What an entry is made of</SectionTitle>
        <div className="overflow-hidden rounded-md border">
          {PARTS.map((part) => (
            <div key={part.label} className="flex flex-wrap gap-x-3 gap-y-0.5 border-b px-3 py-1.5 last:border-b-0">
              <span className="w-16 shrink-0 font-mono text-[9.5px] tracking-wide text-muted-foreground uppercase">
                {part.label}
              </span>
              <span className="min-w-0 text-xs">{part.value}</span>
            </div>
          ))}
        </div>
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          The example is invented. Read together, those parts are a claim about something that exists in the world —
          which is a claim that can be checked.
        </p>
      </section>

      <section>
        <SectionTitle>Checking the citation itself</SectionTitle>
        <div className="flex gap-2.5 rounded-md border p-2.5">
          <ScanSearch className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" aria-hidden />
          <div className="min-w-0">
            <p className="text-xs font-medium">Reference Error Checker</p>
            <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">
              Searches the web for each reference and compares the author, title, publisher and year against what it
              finds. It is what catches a mistyped year, an author who has drifted between drafts, or a citation of
              something that was never published.
            </p>
          </div>
        </div>
        <p className="text-foreground/80 mt-2 leading-relaxed">
          This one needs nothing from you: the reference is all it reads. It is one of the{' '}
          <TopicLink to="assessments" onOpenTopic={onOpenTopic}>
            assessments
          </TopicLink>
          , and what it finds arrives as{' '}
          <TopicLink to="issues" onOpenTopic={onOpenTopic}>
            issues
          </TopicLink>{' '}
          like everything else.
        </p>
      </section>

      <section>
        <SectionTitle>Where a reference stops</SectionTitle>
        <p className="text-foreground/80 leading-relaxed">
          A correct citation is not the same as a true claim.{' '}
          <strong className="text-foreground font-medium">
            A bibliography entry names a source, it does not contain one
          </strong>
          , so checking whether the work you cite actually says what you say it says takes the document itself —{' '}
          <TopicLink to="source-files" onOpenTopic={onOpenTopic}>
            a source file
          </TopicLink>
          .
        </p>
      </section>
    </div>
  );
}
