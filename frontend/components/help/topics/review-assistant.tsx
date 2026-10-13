'use client';

import { DOCUMENT_KINDS, OUTPUTS } from '@/components/results/review-assistant/outputs';
import { ReactNode } from 'react';
import { SectionTitle, TopicLink } from '../help-primitives';
import { HelpTopicBodyProps } from '../topics';

/**
 * The one part of the app that is not about reading your draft on its own: it
 * starts from what other people wrote about it. The outputs and the kinds of
 * document come from the tab's own lists, so the two cannot drift apart.
 */
export function ReviewAssistantTopic({ onOpenTopic }: HelpTopicBodyProps) {
  return (
    <div className="space-y-5">
      <section>
        <SectionTitle>After the reviewers reply</SectionTitle>
        <p className="text-foreground/80 leading-relaxed">
          Every{' '}
          <TopicLink to="assessments" onOpenTopic={onOpenTopic}>
            assessment
          </TopicLink>{' '}
          reads your draft on its own. The Review Assistant starts from{' '}
          <strong className="text-foreground font-medium">what your reviewers wrote about it</strong>, and helps with
          the paperwork of a review round: planning the revision, replying to each reviewer, and checking how much of
          what they asked for the revision covers.
        </p>
      </section>

      <section>
        <SectionTitle>What it can write</SectionTitle>
        <ul className="space-y-1.5">
          {OUTPUTS.map((output) => (
            <Fact key={output.id} term={output.title}>
              {output.description}
            </Fact>
          ))}
        </ul>
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          Pick any of them, in any order and at any point in the round. Picked together, they come from one reading of
          your documents, so every reviewer point keeps the same ID across all of them.
        </p>
      </section>

      <section>
        <SectionTitle>What to give it</SectionTitle>
        <ul className="space-y-1.5">
          {DOCUMENT_KINDS.map((kind) => (
            <Fact key={kind.name} term={kind.name}>
              {kind.description}
            </Fact>
          ))}
        </ul>
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          Upload them, or pick files already in the project, such as an earlier{' '}
          <TopicLink to="revisions" onOpenTopic={onOpenTopic}>
            revision
          </TopicLink>{' '}
          of the main document. You never say which is which: the Review Assistant works it out, and each request lists
          how it read every document so you can catch a misreading. Word comments and tracked changes are read too, so a
          reviewer who only marked up your draft counts as a reviewer.
        </p>
      </section>

      <section>
        <SectionTitle>Where it lives</SectionTitle>
        <ul className="space-y-1.5">
          <Fact term="The Review Assistant tab">
            Start a request, and come back to every earlier one with its outputs and the documents it read.
          </Fact>
          <Fact term="Still in alpha">
            It is behind an opt-in while it settles, which is why it is not in every project.
          </Fact>
        </ul>
      </section>
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
