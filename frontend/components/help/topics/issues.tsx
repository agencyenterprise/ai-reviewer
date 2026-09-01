'use client';

import { SeverityEnum } from '@/lib/generated-api';
import { SEVERITY } from '@/lib/severity-style';
import { cn } from '@/lib/utils';
import { CheckIcon, LightbulbIcon, ThumbsDown, ThumbsUp } from 'lucide-react';
import { ReactNode } from 'react';
import { SectionTitle, TopicLink } from '../help-primitives';
import { HelpTopicBodyProps } from '../topics';

/** What each level means, in the colours the document and the list use. */
const LEVELS: { severity: SeverityEnum; gloss: string }[] = [
  { severity: SeverityEnum.High, gloss: 'Worth fixing before this goes out.' },
  { severity: SeverityEnum.Medium, gloss: 'Worth a look; the assessment is not certain, or the stakes are lower.' },
  { severity: SeverityEnum.Low, gloss: 'A small thing, offered in case you want it.' },
  { severity: SeverityEnum.None, gloss: 'The check ran here and found nothing wrong. Hidden until you ask for it.' },
];

/**
 * What an issue is, shown rather than described: the anatomy below is the same
 * note the margin and the issue list render, so a reader meets the thing itself
 * before being told how to act on it.
 */
export function IssuesTopic({ onOpenTopic }: HelpTopicBodyProps) {
  return (
    <div className="space-y-5">
      <section>
        <SectionTitle>One finding, in one place</SectionTitle>
        <p className="text-foreground/80 leading-relaxed">
          An issue is a single thing an{' '}
          <TopicLink to="assessments" onOpenTopic={onOpenTopic}>
            assessment
          </TopicLink>{' '}
          found, tied to <strong className="text-foreground font-medium">the lines it is about</strong>. That anchor is
          what the document explorer is built on: issues sit in the margin beside their paragraph, and selecting one
          moves the document to it.
        </p>

        <div className="mt-2 overflow-hidden rounded-md border">
          <div className={cn('flex items-start gap-2 border-b px-3 py-2', SEVERITY[SeverityEnum.Medium].wash)}>
            <span className={cn('mt-1.5 block size-1.5 shrink-0 rounded-full', SEVERITY[SeverityEnum.Medium].dot)} />
            <div className="min-w-0">
              <p className="text-xs font-medium">Abbreviation “GER” is used before it is defined</p>
              <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">
                It first appears on line 21, and is spelled out on line 96.
              </p>
            </div>
            <span className="ml-auto shrink-0 font-mono text-[10px] text-muted-foreground">L21</span>
          </div>

          <div className="space-y-2 px-3 py-2">
            <div className="bg-background/60 rounded border border-dashed px-2 py-1.5">
              <p className="mb-1 flex items-center gap-1 font-mono text-[9.5px] tracking-wide text-muted-foreground uppercase">
                <LightbulbIcon className="size-3" aria-hidden />
                Suggested action
              </p>
              <p className="text-xs leading-relaxed">
                Spell the term out at its first use, then use the abbreviation from there on.
              </p>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="bg-primary text-primary-foreground inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium">
                <CheckIcon className="size-3" aria-hidden />
                Mark resolved
              </span>
              <span className="ml-auto flex items-center gap-1 text-muted-foreground">
                <ThumbsUp className="size-3" aria-hidden />
                <ThumbsDown className="size-3" aria-hidden />
              </span>
            </div>
          </div>
        </div>

        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          The example is invented; a real one names the assessment that raised it and often carries further detail
          behind <span className="font-medium">Show details</span>.
        </p>
      </section>

      <section>
        <SectionTitle>How bad it thinks it is</SectionTitle>
        <ul className="space-y-1.5">
          {LEVELS.map((level) => (
            <li key={level.severity} className="flex items-baseline gap-2">
              <span className={cn('mt-1.5 block size-1.5 shrink-0 rounded-full', SEVERITY[level.severity].dot)} />
              <span className="min-w-0 text-xs leading-snug">
                <strong className={cn('font-medium', SEVERITY[level.severity].text)}>
                  {SEVERITY[level.severity].label}
                </strong>{' '}
                <span className="text-muted-foreground">{level.gloss}</span>
              </span>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          Severity is the assessment&apos;s judgement, not a verdict on your draft. Read the ones that matter to you and
          ignore the rest.
        </p>
      </section>

      <section>
        <SectionTitle>What you can do with one</SectionTitle>
        <ul className="space-y-1.5">
          <Fact term="Mark it resolved">
            Once you have dealt with it, or decided not to. Resolved issues drop out of the view and out of the counts,
            and the filter panel brings them back.
          </Fact>
          <Fact
            term={
              <TopicLink to="feedback" onOpenTopic={onOpenTopic}>
                Say whether it was any good
              </TopicLink>
            }
          >
            The thumbs on an issue tell us where an assessment is earning its place and where it is wasting your time.
            Nothing you say there leaves the project until you choose to share it.
          </Fact>
          <Fact term="Narrow the list">
            The filters take the explorer down to one severity or one assessment, which is how a few hundred issues
            become a session&apos;s worth of work.
          </Fact>
        </ul>
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          Issues belong to the{' '}
          <TopicLink to="revisions" onOpenTopic={onOpenTopic}>
            revision
          </TopicLink>{' '}
          they were found in. Re-running an assessment, or uploading a new draft, files the old ones away rather than
          deleting them.
        </p>
      </section>
    </div>
  );
}

function Fact({ term, children }: { term: ReactNode; children: ReactNode }) {
  return (
    <li className="text-xs leading-relaxed">
      <strong className="font-medium">{term}.</strong> <span className="text-muted-foreground">{children}</span>
    </li>
  );
}
