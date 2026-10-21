import { isApiError } from '@/lib/api-error';
import { listChecksApiMicrosoftWordChatChecksGet, PaneCheck } from '@/lib/generated-api';
import { useQuery } from '@tanstack/react-query';
import { useAddinSession } from './session-context';

/** The checks the pane offers to run (`GET /api/microsoft/word/chat/checks`). */
export function usePaneChecks(): PaneCheck[] {
  const { authorize, expire } = useAddinSession();
  const { data } = useQuery({
    queryKey: ['addin-checks'],
    queryFn: async () => {
      try {
        return await listChecksApiMicrosoftWordChatChecksGet({ headers: { Authorization: await authorize() } });
      } catch (error) {
        if (isApiError(error, 401)) expire();
        throw error;
      }
    },
    // The list only changes with a deployment.
    staleTime: Infinity,
    retry: false,
  });
  return data ?? [];
}
