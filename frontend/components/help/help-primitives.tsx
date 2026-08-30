import { ReactNode } from 'react';

/** The label that opens each block of a help topic. */
export function SectionTitle({ children }: { children: ReactNode }) {
  return <h3 className="mb-1.5 font-mono text-[10px] tracking-wide text-muted-foreground uppercase">{children}</h3>;
}
