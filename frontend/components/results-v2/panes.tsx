'use client';

import { Button } from '@/components/ui/button';
import { Sheet, SheetClose, SheetContent, SheetDescription, SheetTitle } from '@/components/ui/sheet';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { WIDE_ENOUGH_FOR_PANE, WIDE_ENOUGH_FOR_RAIL, useMediaQuery } from '@/lib/use-media-query';
import { cn } from '@/lib/utils';
import { PanelLeft, X } from 'lucide-react';
import { ReactNode, useState } from 'react';

export interface RailState {
  /** There is room for the rail to sit beside the content. */
  isWide: boolean;
  isOpen: boolean;
  toggle: () => void;
  close: () => void;
}

/**
 * Whether the rail is showing, and how it shows.
 *
 * Wide enough and it is a column that collapses to nothing; narrower and it is
 * a sheet over the content. Two states rather than one, because the sensible
 * default differs: a column starts open, an overlay starts closed.
 */
export function useRailState(): RailState {
  const isWide = useMediaQuery(WIDE_ENOUGH_FOR_RAIL);
  const [columnOpen, setColumnOpen] = useState(true);
  const [sheetOpen, setSheetOpen] = useState(false);

  return {
    isWide,
    isOpen: isWide ? columnOpen : sheetOpen,
    toggle: () => (isWide ? setColumnOpen((open) => !open) : setSheetOpen((open) => !open)),
    close: () => setSheetOpen(false),
  };
}

/**
 * The left rail: a column beside the content, or a sheet over it. Rendered in
 * one place or the other, never both, so anything stateful inside keeps its
 * state instead of running twice.
 */
export function Rail({ state, label, children }: { state: RailState; label: string; children: ReactNode }) {
  if (state.isWide) {
    return (
      <aside
        className={cn(
          'bg-sidebar hidden shrink-0 border-r transition-[width] xl:block',
          state.isOpen ? 'w-72' : 'w-0 overflow-hidden border-r-0',
        )}
      >
        {children}
      </aside>
    );
  }

  return (
    <Sheet open={state.isOpen} onOpenChange={(open) => !open && state.close()}>
      <SheetContent side="left" showCloseButton={false} className="bg-sidebar w-80 gap-0 p-0 sm:max-w-sm">
        <div className="flex h-10 shrink-0 items-center gap-2 border-b px-4">
          <SheetTitle className="text-xs font-medium">{label}</SheetTitle>
          <SheetDescription className="sr-only">{label}</SheetDescription>
          <SheetClose asChild>
            <Button variant="ghost" size="icon" className="ml-auto size-7" aria-label={`Close ${label.toLowerCase()}`}>
              <X className="size-4" />
            </Button>
          </SheetClose>
        </div>
        <div className="min-h-0 flex-1 overflow-hidden">{children}</div>
      </SheetContent>
    </Sheet>
  );
}

/**
 * The button that shows and hides the rail, in the tab's toolbar.
 *
 * Icon alone where the rail is a column — it is right there, and its heading
 * says what it holds. Icon and label where it is a sheet, since nothing else
 * on screen says what pressing this would bring out.
 */
export function RailToggle({ state, label }: { state: RailState; label: string }) {
  const hint = `${state.isOpen && state.isWide ? 'Hide' : 'Show'} ${label.toLowerCase()}`;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size={state.isWide ? 'icon' : 'xs'}
          className={cn('shrink-0', state.isWide && 'size-7')}
          onClick={state.toggle}
          aria-label={hint}
          aria-pressed={state.isOpen}
        >
          <PanelLeft className={state.isWide ? 'size-4' : 'size-3.5'} />
          {!state.isWide && label}
        </Button>
      </TooltipTrigger>
      <TooltipContent>{hint}</TooltipContent>
    </Tooltip>
  );
}

interface SidePaneProps {
  /** Something is selected, or the reader asked for the pane. */
  open: boolean;
  onClose: () => void;
  /** Names the sheet for screen readers when it opens over the content. */
  label: string;
  /** Shown in the column while nothing is selected. Never in the sheet. */
  empty?: ReactNode;
  className?: string;
  children: ReactNode;
}

/**
 * The right-hand pane: a column beside the content where there is room, and a
 * dismissible sheet over it where there is not. Below that width the pane only
 * appears once the reader asks for it, by selecting a row or pressing the
 * control that opens it.
 */
export function SidePane({ open, onClose, label, empty, className, children }: SidePaneProps) {
  const isWide = useMediaQuery(WIDE_ENOUGH_FOR_PANE);

  if (isWide) {
    // Nothing to show and nothing to say in its place: take no width at all.
    // The document explorer's margin mode relies on this — the issues are
    // already beside the text, so an empty column would only squeeze it.
    if (!open && !empty) return null;

    return (
      <aside className={cn('hidden w-[24rem] shrink-0 border-l lg:block xl:w-[26rem]', className)}>
        {open ? children : empty}
      </aside>
    );
  }

  return (
    <Sheet open={open} onOpenChange={(next) => !next && onClose()}>
      {/* Its own titled bar rather than the sheet's floating close button: that
          button sits exactly where these panes put their own header content,
          and overlapped it. */}
      <SheetContent side="right" showCloseButton={false} className="w-[26rem] gap-0 p-0 sm:max-w-md">
        <div className="flex h-10 shrink-0 items-center gap-2 border-b px-4">
          <SheetTitle className="text-xs font-medium">{label}</SheetTitle>
          <SheetDescription className="sr-only">{label}</SheetDescription>
          <SheetClose asChild>
            <Button variant="ghost" size="icon" className="ml-auto size-7" aria-label={`Close ${label.toLowerCase()}`}>
              <X className="size-4" />
            </Button>
          </SheetClose>
        </div>
        <div className="min-h-0 flex-1 overflow-hidden">{children}</div>
      </SheetContent>
    </Sheet>
  );
}
