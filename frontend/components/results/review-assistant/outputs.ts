import { ReviewAssistantOutput } from '@/lib/generated-api';
import { ClipboardCheck, ListChecks, LucideIcon, MessagesSquare } from 'lucide-react';

export interface OutputDefinition {
  id: ReviewAssistantOutput;
  title: string;
  /** One line on what the output is. */
  description: string;
  /** What it reads, so an author knows what to bring. */
  needs: string;
  icon: LucideIcon;
}

/** In the order an author usually needs them, which is not an order they must follow. */
export const OUTPUTS: OutputDefinition[] = [
  {
    id: ReviewAssistantOutput.RevisionPlanningSummary,
    title: 'Revision plan',
    description: 'Turns reviewer memos and comments into a revision plan: what to change, where, and in which order.',
    needs: 'The draft the reviewers read, and their memos or marked-up copies',
    icon: ListChecks,
  },
  {
    id: ReviewAssistantOutput.ReviewerResponseMemos,
    title: 'Response memos',
    description: "A draft reply to each reviewer that quotes every point and says what you changed, or why you didn't.",
    needs: 'Both drafts, and the reviewer memos or marked-up copies',
    icon: MessagesSquare,
  },
  {
    id: ReviewAssistantOutput.ReviewerCoverageReport,
    title: 'QA coverage report',
    description: "Checks whether the revision answered every reviewer point, and says if it's ready to sign off.",
    needs: 'Both drafts, the reviewer memos or marked-up copies, and any response memos',
    icon: ClipboardCheck,
  },
];

export function outputTitle(output: ReviewAssistantOutput): string {
  return OUTPUTS.find((o) => o.id === output)?.title ?? output;
}

/**
 * What an author might have, named the way the output cards name them.
 * Spelled out because "reviewer memo" and "response memo" are publishing
 * terms not every author uses.
 */
export const DOCUMENT_KINDS = [
  { name: 'Draft', description: 'The version your reviewers read, and your revised version if you have one.' },
  { name: 'Reviewer memo', description: 'The written review a reviewer sent back about your draft.' },
  {
    name: 'Marked-up copy',
    description: "A Word file of your draft with a reviewer's comments or tracked changes in it.",
  },
  { name: 'Response memo', description: 'Your reply to a reviewer, answering their points one by one.' },
];
