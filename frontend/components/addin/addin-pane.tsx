'use client';

import { AddinSession } from '@/components/addin/addin-sign-in';
import { WordChat } from '@/components/addin/chat/word-chat';
import { HandoffList, usePendingHandoffs } from '@/components/addin/handoff-panel';
import { teamsNotice } from '@/lib/addin/teams-notice';
import { isApiError } from '@/lib/api-error';
import { featuresApiMicrosoftWordFeaturesGet } from '@/lib/generated-api';
import { cn } from '@/lib/utils';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

/**
 * The signed-in pane: the chat, and the changes asked for in Teams when this deployment
 * runs the Teams bot. Those take no room until something waits: then a notice above the
 * chat says so, and opens them in the chat's place.
 */
export function AddinPane({ session }: { session: AddinSession }) {
  const features = useQuery({
    queryKey: ['addin-features'],
    queryFn: async () => {
      try {
        return await featuresApiMicrosoftWordFeaturesGet({ headers: { Authorization: await session.authorize() } });
      } catch (error) {
        if (isApiError(error, 401)) session.expire();
        throw error;
      }
    },
    retry: false,
    staleTime: Infinity,
  });
  // Fails open: if the check itself fails (a deploy restarting, say), what waits from Teams
  // is still looked for. The notice shows only when something does, so a deployment
  // without the bot still shows nothing.
  const teams = features.data?.teams ?? features.isError;
  const [showingTeams, setShowingTeams] = useState(false);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {teams && !showingTeams && <TeamsNotice session={session} onReview={() => setShowingTeams(true)} />}
      {showingTeams && (
        <div className="flex min-h-0 flex-1 flex-col">
          <div className="flex items-center gap-2 border-b px-3 py-1.5 text-xs">
            <button type="button" className="text-primary hover:underline" onClick={() => setShowingTeams(false)}>
              ← Chat
            </button>
            <span className="text-muted-foreground">·</span>
            <span className="font-medium">From Teams</span>
          </div>
          <div className="overflow-y-auto">
            <HandoffList session={session} />
          </div>
        </div>
      )}
      {/* Kept mounted behind the Teams list: leaving the chat mid-answer must not drop the
          turn being streamed. */}
      <div className={cn('flex min-h-0 flex-1 flex-col', showingTeams && 'hidden')}>
        <WordChat session={session} />
      </div>
    </div>
  );
}

/** A line above the chat while suggestions from Teams wait; nothing otherwise. */
function TeamsNotice({ session, onReview }: { session: AddinSession; onReview: () => void }) {
  const pending = usePendingHandoffs(session);
  const notice = teamsNotice(pending.data?.here ?? [], pending.data?.elsewhere ?? []);
  if (!notice) return null;
  return (
    <div className="mx-3 mt-2 flex items-center gap-2 rounded-md border border-primary/30 bg-primary/5 px-3 py-1.5 text-xs">
      <span className="flex-1">{notice}</span>
      <button type="button" className="font-medium text-primary hover:underline" onClick={onReview}>
        Review
      </button>
    </div>
  );
}
