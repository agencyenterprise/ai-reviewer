'use client';

import { Eye, EyeOff, FolderOpen, Lock, LucideIcon, ScrollText, ThumbsDown, ThumbsUp } from 'lucide-react';
import { ReactNode } from 'react';
import { SectionTitle, TopicLink } from '../help-primitives';
import { HelpTopicBodyProps } from '../topics';

interface ShareMode {
  icon: LucideIcon;
  /** Worded as the dialog words it, so the two are recognisably the same choice. */
  label: string;
  tag?: string;
  /** What an administrator gets. */
  shared: string;
  /** What stays with you, or null where the mode holds nothing back. */
  withheld: string | null;
}

/**
 * The three answers to "who can see your feedback?", in the order the dialog
 * offers them: least shared first, so the default is the one a reader meets
 * before any of the others.
 */
const SHARE_MODES: ShareMode[] = [
  {
    icon: Lock,
    label: 'Don’t share any information',
    tag: 'Default',
    shared: 'Nothing. The rating is yours, and it stays inside your project.',
    withheld: 'The issue, your note, your document, your files, and every result.',
  },
  {
    icon: ScrollText,
    label: 'Share only this issue information',
    shared: 'The issue itself — its title and description — with your rating and your note.',
    withheld: 'Your document, the files you uploaded, and the rest of the assessment results.',
  },
  {
    icon: FolderOpen,
    label: 'Share whole project information',
    shared: 'All of the above, plus read-only access to the project: the draft, every uploaded file, and every result.',
    withheld: null,
  },
];

/**
 * The thumbs, the note, and what sharing them actually hands over. The
 * privacy question is the one people hesitate on, so the modes are laid out as
 * what an administrator would see rather than as three labels — nobody should
 * have to guess what "share this issue" covers.
 */
export function FeedbackTopic({ onOpenTopic }: HelpTopicBodyProps) {
  return (
    <div className="space-y-5">
      <section>
        <SectionTitle>Rating a finding</SectionTitle>
        <p className="text-foreground/80 leading-relaxed">
          Every{' '}
          <TopicLink to="issues" onOpenTopic={onOpenTopic}>
            issue
          </TopicLink>{' '}
          carries a pair of thumbs. They are how you tell us{' '}
          <strong className="text-foreground font-medium">whether the finding was worth raising</strong> — that an{' '}
          <TopicLink to="assessments" onOpenTopic={onOpenTopic}>
            assessment
          </TopicLink>{' '}
          caught something real, or that it wasted your time on something it misread.
        </p>

        <div className="mt-2 overflow-hidden rounded-md border">
          <div className="flex items-start gap-2 border-b px-3 py-2">
            <div className="min-w-0">
              <p className="text-xs font-medium">Abbreviation “GER” is used before it is defined</p>
              <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">
                It first appears on line 21, and is spelled out on line 96.
              </p>
            </div>
            <span className="ml-auto flex shrink-0 items-center gap-1">
              <span className="rounded border p-1 text-muted-foreground">
                <ThumbsUp className="size-3" aria-hidden />
              </span>
              <span className="bg-primary text-primary-foreground rounded p-1">
                <ThumbsDown className="size-3" aria-hidden />
              </span>
            </span>
          </div>

          <div className="space-y-2 px-3 py-2">
            <p className="text-xs font-medium">What could be improved?</p>
            <p className="bg-background/60 rounded border border-dashed px-2 py-1.5 text-xs leading-relaxed text-muted-foreground italic">
              The term is defined in the caption of Figure 1, which this seems to have skipped.
            </p>
          </div>
        </div>

        <ul className="mt-2 space-y-1.5">
          <Fact term="Thumbs up is one click">Nothing else to fill in. It records that the finding landed.</Fact>
          <Fact term="Thumbs down asks a question">
            <strong className="text-foreground font-medium">What could be improved?</strong> The note is optional, and
            it is the most useful thing you can send: a thumbs down says something is wrong, a note says what.
          </Fact>
          <Fact term="One rating per issue">
            Rating an issue again replaces what you said before, so changing your mind costs nothing.
          </Fact>
        </ul>

        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          Ratings belong to the person whose project it is. Anyone else reading the project — an administrator on a
          shared one, or someone following a share link — sees what was said, and cannot change it.
        </p>
      </section>

      <section>
        <SectionTitle>Who gets to see it</SectionTitle>
        <p className="text-foreground/80 leading-relaxed">
          The first time you rate anything in a project, we ask before saving it. The answer covers{' '}
          <strong className="text-foreground font-medium">the whole project, not that one issue</strong>, and until you
          give one, nothing is shared.
        </p>

        <div className="mt-2 space-y-2">
          {SHARE_MODES.map((mode) => (
            <ModeCard key={mode.label} mode={mode} />
          ))}
        </div>

        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          Only the last two put anything in front of an administrator. On the first, the thumbs still work and the
          ratings are still yours to read — they simply go no further.
        </p>
      </section>

      <section>
        <SectionTitle>What sharing is for</SectionTitle>
        <p className="text-foreground/80 leading-relaxed">
          Shared feedback collects in one list that the people building Draft Detective read, search, and export. It is
          the only direct signal we have about{' '}
          <strong className="text-foreground font-medium">which assessments are earning their place</strong> and which
          keep raising things you did not need — and it is what the next round of changes to them is built on.
        </p>
        <p className="text-foreground/80 mt-2 leading-relaxed">
          Sharing the whole project is worth more than sharing the issue alone, because a finding read without the
          paragraph it came from is often impossible to judge. It also hands over more, which is exactly why the choice
          is yours and the default is to share nothing.
        </p>
      </section>

      <section>
        <SectionTitle>Changing your mind</SectionTitle>
        <p className="text-foreground/80 leading-relaxed">
          The setting lives in the project&apos;s details, under{' '}
          <strong className="text-foreground font-medium">Feedback Visibility</strong>, and it can be changed whenever
          you like. It applies to everything you have already rated in that project, not only to what comes next: turn
          it back to <em>Only me</em> and those ratings stop appearing to administrators, along with the project itself.
        </p>
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          Each project is answered separately. Sharing one says nothing about the others, and a new project starts with
          the question unanswered.
        </p>
      </section>
    </div>
  );
}

function ModeCard({ mode }: { mode: ShareMode }) {
  const { icon: Icon } = mode;

  return (
    <div className="rounded-md border p-2.5">
      <p className="mb-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs font-medium">
        <Icon className="size-3.5 shrink-0 text-muted-foreground" aria-hidden />
        {mode.label}
        {mode.tag && (
          <span className="bg-primary/10 text-primary rounded-sm px-1.5 py-0.5 text-[10px] font-semibold">
            {mode.tag}
          </span>
        )}
      </p>
      <Line icon={Eye} label="Administrators see">
        {mode.shared}
      </Line>
      {mode.withheld && (
        <Line icon={EyeOff} label="Stays with you">
          {mode.withheld}
        </Line>
      )}
    </div>
  );
}

function Line({ icon: Icon, label, children }: { icon: LucideIcon; label: string; children: ReactNode }) {
  return (
    <p className="mt-1 flex gap-1.5 text-xs leading-relaxed text-muted-foreground">
      <Icon className="mt-0.5 size-3 shrink-0" aria-hidden />
      <span className="min-w-0">
        <span className="text-foreground/80 font-medium">{label}:</span> {children}
      </span>
    </p>
  );
}

function Fact({ term, children }: { term: string; children: ReactNode }) {
  return (
    <li className="text-xs leading-relaxed">
      <strong className="font-medium">{term}.</strong> <span className="text-muted-foreground">{children}</span>
    </li>
  );
}
