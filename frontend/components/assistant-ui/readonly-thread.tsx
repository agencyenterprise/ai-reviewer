import { MarkdownText } from '@/components/assistant-ui/elements/markdown-text';
import {
  AssistantMessage,
  ThreadComponentsContext,
  type ThreadComponents,
} from '@/components/assistant-ui/elements/thread.aui';
import { ReasoningSteps } from '@/components/assistant-ui/reasoning-steps';
import { TooltipIconButton } from '@/components/assistant-ui/elements/tooltip-icon-button';
import { cn } from '@/lib/utils';
import { MessagePrimitive, ThreadPrimitive } from '@assistant-ui/react';
import { ArrowDownIcon } from 'lucide-react';
import type { FC } from 'react';

/**
 * A readonly version of the Thread component that displays messages
 * without any interactive features (no composer, no edit, no reload).
 * Useful for displaying conversation history from external sources.
 */
interface ReadonlyThreadProps {
  /**
   * Extra classes for the scroll viewport. Callers that already provide spacing
   * above the thread pass `pt-0` here so the padding does not stack.
   */
  viewportClassName?: string;
}

// The same message slots the chat page passes to Thread, for `AssistantMessage`.
const THREAD_COMPONENTS: ThreadComponents = { ReasoningGroup: ReasoningSteps };

export const ReadonlyThread: FC<ReadonlyThreadProps> = ({ viewportClassName }) => {
  return (
    <ThreadComponentsContext.Provider value={THREAD_COMPONENTS}>
      {/* `AssistantMessage` always renders a footer (copy, regenerate, more) that reserves height under
          every message. A readonly transcript has no actions, so the footer is hidden here. */}
      <ThreadPrimitive.Root
        className="aui-root aui-thread-root @container flex h-full flex-col bg-background [&_[data-slot$=assistant-message-footer]]:hidden"
        style={{
          ['--thread-max-width' as string]: '48rem',
        }}
      >
        <ThreadPrimitive.Viewport
          turnAnchor="top"
          className={cn(
            'aui-thread-viewport relative flex flex-1 flex-col overflow-x-auto overflow-y-scroll scroll-smooth px-4 pt-4',
            viewportClassName,
          )}
        >
          <ThreadPrimitive.Messages
            components={{
              SystemMessage: ReadonlySystemMessage,
              UserMessage: ReadonlyUserMessage,
              AssistantMessage,
            }}
          />

          <ThreadPrimitive.ViewportFooter className="aui-thread-viewport-footer sticky bottom-0 mx-auto mt-auto flex w-full max-w-(--thread-max-width) flex-col gap-4 overflow-visible rounded-t-3xl pb-4 md:pb-6">
            <ThreadScrollToBottom />
          </ThreadPrimitive.ViewportFooter>
        </ThreadPrimitive.Viewport>
      </ThreadPrimitive.Root>
    </ThreadComponentsContext.Provider>
  );
};

const ThreadScrollToBottom: FC = () => {
  return (
    <ThreadPrimitive.ScrollToBottom asChild>
      <TooltipIconButton
        tooltip="Scroll to bottom"
        variant="outline"
        className="aui-thread-scroll-to-bottom absolute -top-12 z-10 self-center rounded-full p-4 disabled:invisible dark:bg-background dark:hover:bg-accent"
      >
        <ArrowDownIcon />
      </TooltipIconButton>
    </ThreadPrimitive.ScrollToBottom>
  );
};

const ReadonlySystemMessage: FC = () => {
  return (
    <MessagePrimitive.Root
      className="aui-system-message-root fade-in slide-in-from-bottom-1 relative mx-auto w-full max-w-(--thread-max-width) animate-in py-3 duration-150"
      data-role="system"
    >
      <div className="wrap-break-word rounded-lg border border-dashed bg-muted/40 px-4 py-3 text-sm leading-relaxed">
        <MessagePrimitive.Parts components={{ Text: MarkdownText }} />
      </div>
    </MessagePrimitive.Root>
  );
};

const ReadonlyUserMessage: FC = () => {
  return (
    <MessagePrimitive.Root
      className="aui-user-message-root fade-in slide-in-from-bottom-1 mx-auto grid w-full max-w-(--thread-max-width) animate-in auto-rows-auto grid-cols-[minmax(72px,1fr)_auto] content-start gap-y-2 px-2 py-3 duration-150 [&:where(>*)]:col-start-2"
      data-role="user"
    >
      <div className="aui-user-message-content-wrapper relative col-start-2 min-w-0">
        <div className="aui-user-message-content wrap-break-word rounded-2xl bg-muted px-4 py-2.5 text-foreground text-sm">
          <MessagePrimitive.Parts components={{ Text: MarkdownText }} />
        </div>
      </div>
    </MessagePrimitive.Root>
  );
};
