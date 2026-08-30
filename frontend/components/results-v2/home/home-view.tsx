'use client';

import { HelpLink } from '@/components/help/help-link';
import { Button } from '@/components/ui/button';
import { useWorkflowTypes } from '@/lib/hooks/use-workflow-types';
import { ArrowRight, FileUp, MessagesSquare, PlayCircle, ScrollText } from 'lucide-react';
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import { ReactNode } from 'react';
import { IssueAnatomy } from './issue-anatomy';
import { QuestionWall } from './question-wall';

const STEPS = [
  {
    icon: FileUp,
    title: 'Bring the draft',
    body: 'A Word file, a PDF, or markdown. Draft Detective converts it, finds its sections, and pulls the bibliography out by itself.',
  },
  {
    icon: PlayCircle,
    title: 'Choose what to ask',
    body: 'Pick the assessments that matter for this piece. They run in the background, in whatever order their inputs require.',
  },
  {
    icon: ScrollText,
    title: 'Read the answers in place',
    body: 'Each finding sits in the margin beside the line it is about, with what to do next. Resolve them as you go.',
  },
  {
    icon: MessagesSquare,
    title: 'Revise, and keep the record',
    body: 'Upload the revision when it is ready. The draft it replaces stays readable, with everything that was found in it.',
  },
];

/**
 * The page a first-time visitor lands on.
 *
 * The catalogue does the explaining rather than a pitch above it: the
 * assessments are already written as questions put to a draft, and a list of
 * the real ones says what this is faster than any sentence about AI-powered
 * review. Everything on the page is either live from the API or a faithful
 * reproduction of a screen, so it cannot drift into promising something the
 * product does not do.
 */
export function HomeView() {
  const session = useSession();
  const signedIn = !!session.data?.user;
  const { workflowTypes } = useWorkflowTypes();
  const available = workflowTypes.filter((type) => !type.is_internal && !type.is_experimental).length;

  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      <div className="mx-auto max-w-4xl px-6 py-16 sm:py-24">
        <header className="max-w-2xl">
          <p className="font-mono text-[11px] tracking-[0.14em] text-muted-foreground uppercase">
            AI-Powered Peer Review
          </p>
          <h1 className="text-primary mt-4 text-5xl leading-[0.95] font-bold tracking-tight sm:text-6xl">
            Draft Detective
          </h1>
          <p className="text-foreground/80 mt-5 text-lg leading-relaxed">
            Transform your document review process with Draft Detective. Run pre-peer review checks on your manuscript
            and get a prioritized list of flagged issues. Built for researchers, analysts, and content reviewers who
            want to catch problems before reviewers do.
          </p>

          <div className="mt-7 flex flex-wrap items-center gap-3">
            <Button size="lg" asChild>
              <Link href={signedIn ? '/new' : '/api/auth/signin'}>
                {signedIn ? 'Start a project' : 'Sign in to start'}
                <ArrowRight className="size-4" />
              </Link>
            </Button>
            {signedIn && (
              <Button size="lg" variant="outline" asChild>
                <Link href="/v2/projects">Your projects</Link>
              </Button>
            )}
          </div>
        </header>

        <Section
          eyebrow="What comes back"
          title="A finding, on the line it is about"
          lede="Nothing is changed in your document. Every assessment only reads, and answers where you are reading."
        >
          <IssueAnatomy />
          <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
            Each finding carries a severity, the assessment that raised it, and a suggested action. Mark it resolved
            when you have dealt with it — or say it was not worth raising, which is how the assessments get better.{' '}
            <HelpLink topic="issues">More about issues</HelpLink>
          </p>
        </Section>

        <Section
          eyebrow={available > 0 ? `${available} assessments` : 'The assessments'}
          title="Every question, put to the draft"
          lede="Each assessment asks one thing and reports only what it finds. Run the ones that matter for this piece."
        >
          <QuestionWall />
        </Section>

        <Section eyebrow="How a project goes" title="Four steps, then again on the next draft">
          <ol className="grid gap-4 sm:grid-cols-2">
            {STEPS.map((step, index) => (
              <li key={step.title} className="rounded-lg border p-4">
                <p className="flex items-center gap-2 text-sm font-medium">
                  <span className="bg-primary/10 text-primary flex size-5 shrink-0 items-center justify-center rounded-full font-mono text-[10px]">
                    {index + 1}
                  </span>
                  <step.icon className="size-3.5 shrink-0 text-muted-foreground" aria-hidden />
                  {step.title}
                </p>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{step.body}</p>
              </li>
            ))}
          </ol>
        </Section>

        <div className="mt-20 rounded-lg border p-6 sm:p-8">
          <h2 className="text-xl font-semibold tracking-tight">Put a draft through it</h2>
          <p className="text-foreground/80 mt-2 max-w-xl text-sm leading-relaxed">
            One document is enough to start. The assessments that need your sources will say so, and the rest run on the
            draft alone.
          </p>
          <Button className="mt-4" asChild>
            <Link href={signedIn ? '/new' : '/api/auth/signin'}>
              {signedIn ? 'Start a project' : 'Sign in to start'}
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

function Section({
  eyebrow,
  title,
  lede,
  children,
}: {
  eyebrow: string;
  title: string;
  lede?: string;
  children: ReactNode;
}) {
  return (
    <section className="mt-20 sm:mt-28">
      <p className="font-mono text-[11px] tracking-[0.14em] text-muted-foreground uppercase">{eyebrow}</p>
      <h2 className="mt-3 text-2xl font-semibold tracking-tight text-balance sm:text-3xl">{title}</h2>
      {lede && <p className="text-foreground/80 mt-3 max-w-2xl leading-relaxed">{lede}</p>}
      <div className="mt-7">{children}</div>
    </section>
  );
}
