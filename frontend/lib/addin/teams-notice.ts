import type { HandoffView } from '@/lib/generated-api';
import { waitingDocuments } from './other-documents';

/**
 * What the pane says above the chat about suggestions waiting from Teams, or null to say
 * nothing. Those for this document come first; others only point to their documents.
 */
export function teamsNotice(here: HandoffView[], elsewhere: HandoffView[]): string | null {
  if (here.length > 0) {
    return `${here.length} ${here.length === 1 ? 'suggestion' : 'suggestions'} from Teams for this document`;
  }
  const documents = waitingDocuments(elsewhere).length;
  if (documents > 0) {
    return `Suggestions from Teams wait on ${documents} other ${documents === 1 ? 'document' : 'documents'}`;
  }
  return null;
}
