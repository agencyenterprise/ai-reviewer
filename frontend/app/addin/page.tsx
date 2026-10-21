'use client';

import { AddinSignIn } from '@/components/addin/addin-sign-in';
import { WordChat } from '@/components/addin/chat/word-chat';
import { HandoffList } from '@/components/addin/handoff-panel';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useOfficeInit } from '@/lib/addin/use-office-init';

export default function AddinPage() {
  const { isInitialized } = useOfficeInit();

  if (!isInitialized) return <div className="p-4 text-center">Loading Add-in...</div>;

  return (
    <div className="flex flex-col h-screen bg-card">
      <AddinSignIn prompt="Sign in to chat with Draft Detective about this document, and to apply changes asked for in Teams.">
        {(session) => (
          <Tabs defaultValue="chat" className="flex min-h-0 flex-1 flex-col gap-0">
            <TabsList className="mx-3 mt-2 w-auto">
              <TabsTrigger value="chat">Chat</TabsTrigger>
              <TabsTrigger value="teams">From Teams</TabsTrigger>
            </TabsList>
            {/* Kept mounted: switching tabs mid-answer must not drop the turn being streamed. */}
            <TabsContent value="chat" forceMount className="flex min-h-0 flex-1 flex-col data-[state=inactive]:hidden">
              <WordChat session={session} />
            </TabsContent>
            <TabsContent value="teams" className="overflow-y-auto">
              <HandoffList session={session} />
            </TabsContent>
          </Tabs>
        )}
      </AddinSignIn>
    </div>
  );
}
