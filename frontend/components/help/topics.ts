import { BookOpen, CircleAlert, FileText, History, ListChecks, LucideIcon } from 'lucide-react';
import { ComponentType } from 'react';
import { AssessmentsTopic } from './topics/assessments';
import { IssuesTopic } from './topics/issues';
import { ReferencesTopic } from './topics/references';
import { RevisionsTopic } from './topics/revisions';
import { SourceFilesTopic } from './topics/source-files';

export type HelpTopicId = 'assessments' | 'issues' | 'references' | 'source-files' | 'revisions';

export interface HelpTopicBodyProps {
  /**
   * Sends the reader to the References tab. Passed only where that is somewhere
   * else to go — the References tab itself omits it.
   */
  onReviewReferences?: () => void;
  /**
   * Moves the dialog to another topic, for the places where one concept hands
   * over to the next rather than repeating it.
   */
  onOpenTopic?: (topic: HelpTopicId) => void;
}

export interface HelpTopic {
  id: HelpTopicId;
  /** In the navigation, where it sits beside the other topics. */
  label: string;
  /** The dialog's heading once this topic is open. */
  title: string;
  description: string;
  icon: LucideIcon;
  Body: ComponentType<HelpTopicBodyProps>;
}

/**
 * The concepts the app explains in one place, ordered as the work runs:
 * assessments produce issues, references name sources, one assessment needs
 * those sources, and revisions are what all of it hangs from. Every "what is this" link in the product opens
 * this list at one of them, so a question asked in one corner is answered next
 * to all the others.
 */
export const HELP_TOPICS: HelpTopic[] = [
  {
    id: 'assessments',
    label: 'Assessments',
    title: 'Assessments, and what they check',
    description: 'Each one reads your draft looking for a different kind of problem, and reports what it finds.',
    icon: ListChecks,
    Body: AssessmentsTopic,
  },
  {
    id: 'issues',
    label: 'Issues',
    title: 'Issues in your document',
    description: 'One finding from one assessment, anchored to the lines it is about.',
    icon: CircleAlert,
    Body: IssuesTopic,
  },
  {
    id: 'references',
    label: 'References',
    title: 'References in your bibliography',
    description: 'Every entry, pulled out of your document automatically.',
    icon: BookOpen,
    Body: ReferencesTopic,
  },
  {
    id: 'source-files',
    label: 'Source files',
    title: 'Source files, and the assessment that needs them',
    description:
      'The document a reference points at. It does not arrive with your draft, so someone has to provide it.',
    icon: FileText,
    Body: SourceFilesTopic,
  },
  {
    id: 'revisions',
    label: 'Revisions',
    title: 'Revisions of the main document',
    description: 'Each draft you upload becomes a revision. The ones before it stay, with everything they found.',
    icon: History,
    Body: RevisionsTopic,
  },
];
