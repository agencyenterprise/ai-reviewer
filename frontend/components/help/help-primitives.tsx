import { ReactNode } from 'react';
import type { HelpTopicId } from './topics';

/** The label that opens each block of a help topic. */
export function SectionTitle({ children }: { children: ReactNode }) {
  return <h3 className="mb-1.5 font-mono text-[10px] tracking-wide text-muted-foreground uppercase">{children}</h3>;
}

/**
 * A word in one topic that is explained in another. Falls back to plain text
 * when the dialog has not passed a navigator, so a body stays readable wherever
 * it is rendered.
 */
export function TopicLink({
  to,
  onOpenTopic,
  children,
}: {
  to: HelpTopicId;
  onOpenTopic?: (topic: HelpTopicId) => void;
  children: ReactNode;
}) {
  if (!onOpenTopic) return <>{children}</>;

  return (
    <button
      type="button"
      onClick={() => onOpenTopic(to)}
      className="cursor-pointer underline underline-offset-2 hover:text-foreground"
    >
      {children}
    </button>
  );
}
