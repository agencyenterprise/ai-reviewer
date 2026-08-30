'use client';

import { cn } from '@/lib/utils';
import { CircleStop, FileText, LucideIcon, PlayCircle, Upload } from 'lucide-react';
import { ReactNode } from 'react';
import { SectionTitle } from '../help-primitives';

interface Version {
  label: string;
  tag?: string;
  file: string;
  note: string;
  current?: boolean;
}

/** Newest first, the way the revision menu lists them. */
const STACK: Version[] = [
  {
    label: 'Revision 2',
    tag: 'Current',
    file: 'manuscript-v2.docx',
    note: 'What the explorer shows and what assessments read.',
    current: true,
  },
  {
    label: 'Revision 1',
    file: 'manuscript-v1.docx',
    note: 'Kept as it was, with the issues and results it had.',
  },
];

/** What creating a revision sets in motion, in the order it happens. */
const STEPS: { icon: LucideIcon; title: string; body: string }[] = [
  {
    icon: Upload,
    title: 'Your new file becomes the current revision',
    body: 'The draft you upload is numbered next and takes over the project view. The one it replaces is not overwritten.',
  },
  {
    icon: CircleStop,
    title: 'Work still running on the old draft stops',
    body: 'Anything mid-run would be reporting on a document nobody is reading any more, so it is cancelled rather than finished.',
  },
  {
    icon: PlayCircle,
    title: 'The assessments that ran before run again',
    body: 'On the new draft, unless you clear that option while uploading. Peer Review is the exception: you start it yourself, once the memos for the draft are in.',
  },
];

/**
 * What a revision is and what one costs to make. The question underneath is
 * always the same — what happens to everything I have already done — so the
 * answer leads: the earlier draft and its results stay exactly where they were.
 */
export function RevisionsTopic() {
  return (
    <div className="space-y-5">
      <section>
        <SectionTitle>One project, several drafts</SectionTitle>
        <p className="text-foreground/80 leading-relaxed">
          A revision is a version of the main document. Uploading a new one does not replace what came before it —{' '}
          <strong className="text-foreground font-medium">every earlier revision stays readable</strong>, alongside the
          issues and results it collected. The revision menu in the header is how you move between them.
        </p>

        <div className="mt-2 overflow-hidden rounded-md border">
          {STACK.map((version) => (
            <div
              key={version.label}
              className={cn(
                'flex flex-wrap items-baseline gap-x-2.5 gap-y-1 border-b px-3 py-2 last:border-b-0',
                version.current && 'bg-primary/5',
              )}
            >
              <span className="text-xs font-medium">{version.label}</span>
              {version.tag && (
                <span className="bg-primary/10 text-primary rounded-sm px-1.5 py-0.5 text-[10px] font-semibold">
                  {version.tag}
                </span>
              )}
              {/* Inline rather than a nested flex: a flex box takes its baseline
                  from its first item, and an icon has none, which drops the name
                  below the line the rest of the row sits on. */}
              <span className="min-w-0 font-mono text-[11px] text-muted-foreground">
                <FileText className="mr-1.5 inline size-3 align-[-0.15em]" aria-hidden />
                {version.file}
              </span>
              <span className="text-foreground/80 basis-full text-xs sm:basis-auto">{version.note}</span>
            </div>
          ))}
        </div>

        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          Reading an earlier revision is read-only. Nothing there can be edited, resolved, or re-run — it is a record of
          where the draft stood.
        </p>
      </section>

      <section>
        <SectionTitle>Creating one</SectionTitle>
        <div className="space-y-2">
          {STEPS.map((step) => (
            <Step key={step.title} icon={step.icon} title={step.title}>
              {step.body}
            </Step>
          ))}
        </div>
      </section>

      <section>
        <SectionTitle>What the other files do</SectionTitle>
        <ul className="space-y-1.5">
          <Fact term="Source files">
            Shared by every revision. Provide a reference&apos;s source once and later drafts inherit it, so a new
            revision does not send you back to the References tab.
          </Fact>
          <Fact term="Reviewer memos">
            Belong to the revision they were written about, because that is the draft their author read.
          </Fact>
        </ul>
      </section>
    </div>
  );
}

function Step({ icon: Icon, title, children }: { icon: LucideIcon; title: string; children: ReactNode }) {
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

function Fact({ term, children }: { term: string; children: ReactNode }) {
  return (
    <li className="text-xs leading-relaxed">
      <strong className="font-medium">{term}.</strong> <span className="text-muted-foreground">{children}</span>
    </li>
  );
}
