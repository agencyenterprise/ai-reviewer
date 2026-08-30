'use client';

import { Button } from '@/components/ui/button';
import { SeverityEnum } from '@/lib/generated-api';
import { SEVERITY } from '@/lib/severity-style';
import { cn } from '@/lib/utils';
import { ArrowRight, FileText, FileX2, Globe, LucideIcon, Upload } from 'lucide-react';
import { ReactNode } from 'react';
import { SectionTitle } from '../help-primitives';
import { HelpTopicBodyProps } from '../topics';

interface Verdict {
  severity: SeverityEnum;
  label: string;
  gloss: string;
}

interface Trace {
  /** The sentence without its citation, which is rendered separately. */
  claim: string;
  /** The in-text citation, highlighted in the claim and naming the reference. */
  citation: string;
  reference: string;
  /** The matched source document, or null when the reference has none yet. */
  source: string | null;
  verdict: Verdict;
}

/**
 * Two worked examples, identical but for the last link in the chain. Side by
 * side they make the point the prose cannot: the source document is the only
 * thing standing between a citation and a real verdict.
 *
 * The references are invented. A fabricated claim hung on a real paper would
 * read as a finding about that paper.
 */
const TRACES: Trace[] = [
  {
    claim: 'Training compute for frontier models has doubled roughly every six months since 2020',
    citation: '(Sandoval & Okoye, 2023)',
    reference: 'Sandoval, R., & Okoye, T. (2023). Compute trends in large-scale training.',
    source: 'sandoval-2023.pdf',
    verdict: {
      severity: SeverityEnum.None,
      label: 'Supported',
      gloss: 'The source reports the same doubling time.',
    },
  },
  {
    claim: 'Grid-scale storage now covers 40% of peak demand across three EU member states',
    citation: '(Lindqvist, 2022)',
    reference: 'Lindqvist, A. (2022). European storage deployment review.',
    source: null,
    verdict: {
      severity: SeverityEnum.Medium,
      label: 'Unverifiable',
      gloss: 'With nothing to read, the claim goes unchecked.',
    },
  },
];

/** The full result vocabulary, in the colours the margin and issue list use. */
const OUTCOMES: Verdict[] = [
  { severity: SeverityEnum.None, label: 'Supported', gloss: 'The source backs the claim.' },
  { severity: SeverityEnum.Medium, label: 'Partially supported', gloss: 'It backs part of it.' },
  { severity: SeverityEnum.High, label: 'Unsupported', gloss: 'It does not back the claim.' },
  { severity: SeverityEnum.Medium, label: 'Unverifiable', gloss: 'There was nothing to check against.' },
];

/**
 * The document behind a reference, and why one assessment cannot work without
 * it. The examples carry the argument: side by side, the only thing separating
 * a real verdict from an unverifiable one is whether we hold the source.
 */
export function SourceFilesTopic({ onReviewReferences, onOpenTopic }: HelpTopicBodyProps) {
  return (
    <div className="space-y-5">
      <section>
        <SectionTitle>The document behind a reference</SectionTitle>
        <p className="text-foreground/80 leading-relaxed">
          A source file is the actual paper, report or page that one of your{' '}
          {onOpenTopic ? (
            <button
              onClick={() => onOpenTopic('references')}
              className="cursor-pointer underline underline-offset-2 hover:text-foreground"
            >
              references
            </button>
          ) : (
            'references'
          )}{' '}
          points at. It does not arrive with your draft, because{' '}
          <strong className="text-foreground font-medium">
            a bibliography entry names a source, it does not contain one
          </strong>
          . The References tab says, for each reference, whether one has been provided.
        </p>
        <p className="text-foreground/80 mt-2 leading-relaxed">
          <strong className="text-foreground font-medium">Claim Reference Validation</strong> is the assessment that
          needs them. It reads the document behind each citation and compares it to the claim you hung on it, which is
          not something a bibliography entry can answer.
        </p>
      </section>

      <section>
        <SectionTitle>Why the file matters</SectionTitle>
        <div className="space-y-2">
          {TRACES.map((trace) => (
            <TraceCard key={trace.citation} trace={trace} />
          ))}
        </div>
        <p className="text-foreground/80 mt-2 leading-relaxed">
          Both citations are perfectly good, and both would pass a check of the reference itself. Only one can be read
          against its source.
        </p>
      </section>

      <section>
        <SectionTitle>What comes back</SectionTitle>
        <ul className="grid gap-x-6 gap-y-1.5 sm:grid-cols-2">
          {OUTCOMES.map((outcome) => (
            <li key={outcome.label} className="flex items-baseline gap-2">
              <span className={cn('mt-1.5 block size-1.5 shrink-0 rounded-full', SEVERITY[outcome.severity].dot)} />
              <span className="min-w-0 text-xs leading-snug">
                <strong className="font-medium">{outcome.label}</strong>{' '}
                <span className="text-muted-foreground">{outcome.gloss}</span>
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <SectionTitle>Giving a reference its source</SectionTitle>
        <p className="text-foreground/80 leading-relaxed">
          On the References tab, every reference is listed with the source matched to it. There are two ways to close a
          gap.
        </p>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          <Route icon={Globe} title="Fetch from the web">
            Draft Detective searches the web for the reference and downloads the full text when it finds one it can
            read.
          </Route>
          <Route icon={Upload} title="Upload it yourself">
            Plenty of sources are private, paywalled, or closed to automated downloads. Add the file and we match it to
            the reference.
          </Route>
        </div>
        <p className="text-foreground/80 mt-2 leading-relaxed">
          Then choose <strong className="text-foreground font-medium">Approve and Start Analysis</strong>. Approving
          with gaps is fine: those claims come back{' '}
          <strong className="text-foreground font-medium">unverifiable instead of checked</strong>, and everything else
          runs normally.
        </p>
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          Source files are shared across revisions, so this is not work you repeat on the next draft.
        </p>

        {onReviewReferences && (
          <Button size="sm" className="mt-3" onClick={onReviewReferences}>
            Review references
          </Button>
        )}
      </section>
    </div>
  );
}

function TraceCard({ trace }: { trace: Trace }) {
  const style = SEVERITY[trace.verdict.severity];

  return (
    <div className="overflow-hidden rounded-md border">
      <div className="grid items-start gap-x-3 gap-y-3 p-3 sm:grid-cols-[1fr_auto_1fr_auto_9.5rem]">
        <Cell label="Claim in your document">
          <span className="italic">
            “{trace.claim}{' '}
            {/* Marked the way the document itself marks flagged text, so the
                citation reads as the hinge between claim and reference. */}
            <span className="text-foreground font-medium not-italic underline decoration-dotted decoration-muted-foreground/60 underline-offset-2">
              {trace.citation}
            </span>
            .”
          </span>
        </Cell>
        <Arrow />
        <Cell label="Reference it points to">{trace.reference}</Cell>
        <Arrow />
        <Cell label="Source document">
          {trace.source ? (
            <span className="inline-flex items-center gap-1.5">
              <FileText className="size-3 shrink-0" />
              <span className="truncate font-mono text-[11px]">{trace.source}</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-amber-700 dark:text-amber-400">
              <FileX2 className="size-3 shrink-0" />
              Not provided yet
            </span>
          )}
        </Cell>
      </div>

      <div className={cn('flex flex-wrap items-center gap-x-2 gap-y-0.5 border-t px-3 py-1.5', style.wash)}>
        <span className={cn('block size-1.5 shrink-0 rounded-full', style.dot)} />
        <span className={cn('font-mono text-[10px] tracking-wide uppercase', style.text)}>{trace.verdict.label}</span>
        <span className="text-foreground/80 text-xs">{trace.verdict.gloss}</span>
      </div>
    </div>
  );
}

function Cell({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <p className="mb-0.5 font-mono text-[9.5px] tracking-wide text-muted-foreground uppercase">{label}</p>
      <p className="text-xs leading-snug">{children}</p>
    </div>
  );
}

/** Points right across the columns, down between them once they stack. */
function Arrow() {
  return <ArrowRight className="mt-4 hidden size-3.5 shrink-0 text-muted-foreground sm:block" aria-hidden />;
}

/** One of the two ways to give a reference its source. */
function Route({ icon: Icon, title, children }: { icon: LucideIcon; title: string; children: ReactNode }) {
  return (
    <div className="rounded-md border p-2.5">
      <p className="mb-1 flex items-center gap-1.5 text-xs font-medium">
        <Icon className="size-3.5 shrink-0 text-muted-foreground" aria-hidden />
        {title}
      </p>
      <p className="text-xs leading-relaxed text-muted-foreground">{children}</p>
    </div>
  );
}
