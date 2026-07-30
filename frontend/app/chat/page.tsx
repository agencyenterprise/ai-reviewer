import { ChatAssistant } from '@/components/chat/chat-assistant';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Chat · Draft Detective',
  description: 'Simple chat with an LLM.',
};

export default function ChatPage() {
  return <ChatAssistant />;
}
