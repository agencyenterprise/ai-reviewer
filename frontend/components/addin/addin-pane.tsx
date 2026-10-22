'use client';

import { AddinSession } from '@/components/addin/addin-sign-in';
import { WordChat } from '@/components/addin/chat/word-chat';
import { HandoffList } from '@/components/addin/handoff-panel';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { isApiError } from '@/lib/api-error';
import { featuresApiMicrosoftWordFeaturesGet } from '@/lib/generated-api';
import { useQuery } from '@tanstack/react-query';

/**
 * The signed-in pane: the chat, and the changes asked for in Teams beside it when this
 * deployment runs the Teams bot. Without the bot nothing can ever arrive from Teams, so
 * that tab, and the tab bar with it, is left out.
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
  const teams = features.data?.teams === true;

  return (
    <Tabs defaultValue="chat" className="flex min-h-0 flex-1 flex-col gap-0">
      {teams && (
        <TabsList className="mx-3 mt-2 w-auto">
          <TabsTrigger value="chat">Chat</TabsTrigger>
          <TabsTrigger value="teams">From Teams</TabsTrigger>
        </TabsList>
      )}
      {/* Kept mounted: switching tabs mid-answer must not drop the turn being streamed,
          and neither must the tab bar appearing once the features are known. */}
      <TabsContent value="chat" forceMount className="flex min-h-0 flex-1 flex-col data-[state=inactive]:hidden">
        <WordChat session={session} />
      </TabsContent>
      {teams && (
        <TabsContent value="teams" className="overflow-y-auto">
          <HandoffList session={session} />
        </TabsContent>
      )}
    </Tabs>
  );
}
